import argparse
from pathlib import Path

from .core import ROOT, load_config, run


def main():
    parser = argparse.ArgumentParser(description="A0 synthetic mock or development smoke (maximum 10). Run from repo root.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=ROOT / "src/data/processed/sr_bh_v1/development.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=6)
    args = parser.parse_args()
    try:
        result = run(args.input, args.output, load_config(args.config), args.limit)
    except (ValueError, OSError, KeyError) as exc:
        # No provider body or credential-bearing exception is printed.
        parser.exit(2, f"A0 stopped: {type(exc).__name__}; check input/config/environment and handoff.\n")
    print(result)


if __name__ == "__main__":
    main()
