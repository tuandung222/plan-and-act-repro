#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute a Jupyter notebook end-to-end.")
    parser.add_argument("--input", required=True, help="Input notebook path")
    parser.add_argument("--output", required=True, help="Executed notebook output path")
    parser.add_argument("--timeout", type=int, default=300, help="Per-cell timeout seconds")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Notebook not found: {input_path}")

    nb = nbformat.read(input_path, as_version=4)
    client = NotebookClient(
        nb,
        timeout=args.timeout,
        kernel_name="python3",
        allow_errors=False,
    )
    client.execute(cwd=str(input_path.parent.parent))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, output_path)
    print(f"Notebook executed successfully: {output_path}")


if __name__ == "__main__":
    main()
