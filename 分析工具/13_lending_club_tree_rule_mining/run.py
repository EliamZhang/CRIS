"""???????????????????????"""
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.lending_club_tree_rule_mining import consolidate_csv_outputs, build_config, parse_args, run


def main() -> None:
    args = parse_args()
    config = build_config(args)
    run(config)
    consolidate_csv_outputs(Path(config.output_dir))


if __name__ == "__main__":
    main()
