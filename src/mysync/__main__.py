"""File synchronizer.

This microserver watches pairs of files and sync them as modification happens. The files
are watched by watchdog (a Python library) and sync is done by unison, which are both
dependencies that need to be installed.

For example,

  $ mysync -l file1 file2 -l file3 file4

"""

from argparse import ArgumentParser
from pathlib import Path

from .mysync import Link, check_requirements, serve_forever


def main() -> None:
    check_requirements()

    p = ArgumentParser(description=__doc__)
    p.add_argument("--link", "-l", nargs=2, type=Path, action="append")

    args = p.parse_args()

    links = [Link(*pair) for pair in (args.link or [])]
    serve_forever(links)


if __name__ == "__main__":
    raise SystemExit(main())
