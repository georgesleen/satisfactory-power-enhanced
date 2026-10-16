"""Tests stable wiki extraction and the checked-in source contract."""

import json
import math
import unittest
from pathlib import Path

from extract_buildings import extract


class ExtractionTests(unittest.TestCase):
    def test_stable_buildings_and_variable_recipes(self):
        buildings = {
            "Desc_ConstructorMk1_C": [
                {"stable": False, "powerUsage": 999},
                {"stable": True, "name": "Constructor", "powerUsage": 4,
                 "powerGenerated": 0, "overclockable": True}],
            "Desc_HadronCollider_C": [{"stable": True, "name": "Particle Accelerator",
                "powerUsage": 0, "powerGenerated": 0, "overclockable": True}],
            "Desc_GeneratorCoal_C": [{"stable": True, "name": "Coal-Powered Generator",
                "powerUsage": 0, "powerGenerated": 75, "overclockable": True}],
            "Desc_Wall_C": [{"stable": True, "name": "Wall", "powerUsage": 0,
                "powerGenerated": 0, "overclockable": False}],
        }
        recipes = {"Recipe_Pasta_C": [{"stable": True, "name": "Nuclear Pasta",
            "producedIn": ["Desc_HadronCollider_C"], "duration": 120,
            "minPower": 500, "maxPower": 1500}]}
        table = extract(buildings, recipes, "wiki test")
        self.assertEqual(table["buildings"]["Build_ConstructorMk1_C"]["powerMegawatts"], 4)
        self.assertEqual(table["buildings"]["Build_GeneratorCoal_C"]["generatorMegawatts"], 75)
        self.assertEqual(table["buildings"]["Build_HadronCollider_C"]["powerExponent"], math.log2(2.5))
        self.assertNotIn("Build_Wall_C", table["buildings"])
        self.assertEqual(table["variableRecipes"]["Recipe_Pasta_C"]["maxMegawatts"], 1500)
        self.assertEqual(table["variableRecipes"]["Recipe_Pasta_C"]["durationSeconds"], 120)

    def test_checked_in_wiki_source_and_scenario_references(self):
        root = Path(__file__).parent
        table = json.loads((root / "buildings.json").read_text())
        self.assertIn("satisfactory.wiki.gg", table["source"])
        for path in (root / "scenarios").glob("*.json"):
            for block in json.loads(path.read_text()).get("blocks", []):
                self.assertIn(block["building"], table["buildings"])
                if "recipe" in block:
                    recipe = table["variableRecipes"][block["recipe"]]
                    self.assertEqual(recipe["building"], block["building"])


if __name__ == "__main__":
    unittest.main()
