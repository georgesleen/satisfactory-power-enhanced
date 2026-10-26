"""Export a named EnhancedPower Blender asset."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import epexport

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('asset', type=Path)
parser.add_argument('--blend', type=Path)
parser.add_argument('--output', type=Path)
parser.add_argument('--texture-size', type=int, default=2048)
parser.add_argument('--skip-renders', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
epexport.export_asset(args.asset.resolve(), args.blend, args.output,
                      args.texture_size, not args.skip_renders)
