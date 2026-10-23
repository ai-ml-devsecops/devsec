#!/usr/bin/env python3
"""Print only the pull requests (title + file diffs) from a dependabot dry-run log."""
import sys


def is_diff_line(line):
    return line.startswith("    ")


def main(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()

    count = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        # A PR title is a " => " line directly followed by an indented "± file" diff.
        nxt = next((l for l in lines[i + 1:i + 3] if l.strip()), "")
        if line.startswith(" => ") and nxt.startswith("    ±"):
            count += 1
            print(f"--- PR {count}: {line[4:]}")
            i += 1
            while i < len(lines) and (not lines[i].strip() or is_diff_line(lines[i])):
                if lines[i].strip():
                    print(lines[i])
                i += 1
            print()
            continue
        i += 1

    print(f"{count} pull request(s)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: filter-dry-run-prs.py <dry-run.log>")
    main(sys.argv[1])
