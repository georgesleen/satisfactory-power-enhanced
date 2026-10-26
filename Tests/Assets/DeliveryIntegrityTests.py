"""Exercise the real host preflight's manifest and hash contract, not FBX, PNG or Blender validation.

Payloads are deliberately opaque fixture bytes. A fixture's declared PASS tests metadata handling only;
it does not assert that the payload is a valid mesh, texture or successful Blender bake.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


IMPORTER = Path(__file__).resolve().parents[2] / "assets/common/unreal_import_smoke.py"
BODY = "SM_integrity_Body.fbx"
MOVING_PART = "SM_integrity_Handle.fbx"
COMPLETION = "delivery-complete.json"
IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
DECLARED_PASS = {"status": "PASS", "failures": [], "scope": "Integrity fixture declaration, not format/bake validation"}
COLOR_SPACES = {"BaseColor": "sRGB", "Normal": "Non-Color", "AOMasks": "Non-Color", "ReflectionMap": "Non-Color"}


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def change_json(path, change):
    value = json.loads(path.read_text(encoding="utf-8"))
    change(value)
    write_json(path, value)


class DeliveryIntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="enhancedpower-integrity-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.package = self.directory / "package"
        (self.package / "textures").mkdir(parents=True)
        payloads = {
            BODY: b"opaque body payload\x00\x01",
            MOVING_PART: b"opaque moving-part payload\x02\x03",
            **{f"textures/{name}.png": f"opaque {name} payload".encode("ascii") for name in COLOR_SPACES},
        }
        for name, contents in payloads.items():
            (self.package / name).write_bytes(contents)
        self.products = {name: file_hash(self.package / name) for name in payloads}
        write_json(self.package / "assembly.json", {
            "schema": 2,
            "body_file": BODY,
            "validation_manifest": "validation.json",
            "generic_blender_bake_validation": DECLARED_PASS,
            "product_files_sha256": self.products,
            "static_meshes": {
                "Body": {"file": BODY, "parent": None, "relative_transform_cm": IDENTITY},
                "Handle": {"file": MOVING_PART, "parent": "Body", "relative_transform_cm": IDENTITY},
            },
        })
        write_json(self.package / "validation.json", {
            "generic_blender_bake_validation": DECLARED_PASS,
            "files_sha256": {**self.products, "assembly.json": file_hash(self.package / "assembly.json")},
            "texture_color_spaces": COLOR_SPACES,
        })
        write_json(self.package / COMPLETION, {
            "schema": 1,
            "asset": "integrity",
            "status": "COMPLETE",
            "generic_blender_bake_validation": DECLARED_PASS,
            "renders_skipped": False,
            "files_sha256": {
                **self.products,
                "assembly.json": file_hash(self.package / "assembly.json"),
                "validation.json": file_hash(self.package / "validation.json"),
            },
        })

    def run_preflight(self, environment):
        return subprocess.run(
            [sys.executable, "-I", "-S", str(IMPORTER)],
            env=environment,
            cwd=self.directory,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def final_preflight(self):
        return self.run_preflight({"EP_UNREAL_DELIVERY": str(self.package)})

    def assert_refused(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "", result.stdout)
        self.assertTrue(result.stderr.startswith("EP_UNREAL_DELIVERY_REFUSED "), result.stderr)

    def verified_summary(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "", result.stderr)
        marker, separator, payload = result.stdout.partition(" ")
        self.assertEqual(marker, "EP_UNREAL_DELIVERY_VERIFIED")
        self.assertEqual(separator, " ")
        return json.loads(payload)

    def rehash_metadata(self):
        change_json(self.package / COMPLETION, lambda value: value["files_sha256"].update({
            name: file_hash(self.package / name) for name in ("assembly.json", "validation.json")
        }))

    def test_completed_matching_package(self):
        summary = self.verified_summary(self.final_preflight())
        self.assertEqual(summary["scope"], "FINAL_PACKAGE")
        self.assertEqual(summary["files_sha256"], json.loads((self.package / COMPLETION).read_text())["files_sha256"])
        self.assertFalse(summary["renders_skipped"])

    def test_missing_completion(self):
        (self.package / COMPLETION).unlink()
        self.assert_refused(self.final_preflight())

    def test_started_completion(self):
        change_json(self.package / COMPLETION, lambda value: value.update({"status": "STARTED"}))
        self.assert_refused(self.final_preflight())

    def test_failed_validation_even_with_current_metadata_hashes(self):
        failure = {**DECLARED_PASS, "status": "FAIL", "failures": ["fixture failure"]}
        for name in ("assembly.json", "validation.json", COMPLETION):
            change_json(self.package / name, lambda value: value.update({"generic_blender_bake_validation": failure}))
        self.rehash_metadata()
        self.assert_refused(self.final_preflight())

    def test_corrupted_mesh_with_stale_pass(self):
        path = self.package / BODY
        path.write_bytes(path.read_bytes() + b"interrupted replacement")
        self.assert_refused(self.final_preflight())

    def test_missing_listed_mesh(self):
        (self.package / MOVING_PART).unlink()
        self.assert_refused(self.final_preflight())

    def test_missing_listed_texture(self):
        (self.package / "textures/AOMasks.png").unlink()
        self.assert_refused(self.final_preflight())

    def test_corrupted_texture_with_stale_pass(self):
        (self.package / "textures/Normal.png").write_bytes(b"interrupted normal-map bytes")
        self.assert_refused(self.final_preflight())

    def test_orphan_mesh(self):
        (self.package / "SM_integrity_Obsolete.fbx").write_bytes(b"obsolete payload")
        self.assert_refused(self.final_preflight())

    def test_orphan_texture(self):
        (self.package / "textures/Obsolete.png").write_bytes(b"obsolete payload")
        self.assert_refused(self.final_preflight())

    def test_stale_per_product_hashes_in_validly_hashed_metadata(self):
        stale = {BODY: file_hash(self.package / MOVING_PART)}
        change_json(self.package / "assembly.json", lambda value: value["product_files_sha256"].update(stale))
        change_json(self.package / "validation.json", lambda value: value["files_sha256"].update({
            **stale, "assembly.json": file_hash(self.package / "assembly.json"),
        }))
        self.rehash_metadata()
        self.assert_refused(self.final_preflight())

    def test_missing_render_skip_declaration(self):
        change_json(self.package / COMPLETION, lambda value: value.pop("renders_skipped"))
        self.assert_refused(self.final_preflight())

    def test_skipped_renders_are_reported_without_requiring_render_files(self):
        change_json(self.package / COMPLETION, lambda value: value.update({"renders_skipped": True}))
        self.assertTrue(self.verified_summary(self.final_preflight())["renders_skipped"])

    def test_package_path_escape(self):
        outside = self.directory / "outside.fbx"
        outside.write_bytes(b"outside payload")
        change_json(self.package / COMPLETION, lambda value: value["files_sha256"].update({
            "../outside.fbx": file_hash(outside),
        }))
        self.assert_refused(self.final_preflight())

    def test_assembly_changed_after_completion(self):
        change_json(self.package / "assembly.json", lambda value: value["static_meshes"]["Handle"].update({
            "relative_transform_cm": [[1, 0, 0, 3], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        }))
        self.assert_refused(self.final_preflight())

    def early_environment(self, expected_hash):
        return {"EP_UNREAL_EARLY_FBX": str(self.package / BODY), "EP_UNREAL_EARLY_SHA256": expected_hash}

    def test_early_verified_raw_input_has_nonfinal_scope(self):
        environment = self.early_environment(file_hash(self.package / BODY))
        (self.package / COMPLETION).unlink()
        summary = self.verified_summary(self.run_preflight(environment))
        self.assertEqual(summary["scope"], "EARLY_NONFINAL_DIAGNOSTIC")
        self.assertEqual(summary["files_sha256"], {str(self.package / BODY): environment["EP_UNREAL_EARLY_SHA256"]})

    def test_early_wrong_hash(self):
        self.assert_refused(self.run_preflight(self.early_environment(file_hash(self.package / MOVING_PART))))

    def test_early_missing_expected_hash(self):
        self.assert_refused(self.run_preflight({"EP_UNREAL_EARLY_FBX": str(self.package / BODY)}))

    def test_no_mode(self):
        self.assert_refused(self.run_preflight({}))

    def test_both_modes(self):
        environment = {"EP_UNREAL_DELIVERY": str(self.package), **self.early_environment(file_hash(self.package / BODY))}
        self.assert_refused(self.run_preflight(environment))


if __name__ == "__main__":
    unittest.main()
