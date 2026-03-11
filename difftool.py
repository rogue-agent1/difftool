#!/usr/bin/env python3
"""difftool - Side-by-side and unified diff viewer with color.

Single-file, zero-dependency CLI.
"""

import sys
import argparse
import difflib


def cmd_unified(args):
    with open(args.file1) as f: a = f.readlines()
    with open(args.file2) as f: b = f.readlines()
    diff = difflib.unified_diff(a, b, fromfile=args.file1, tofile=args.file2, n=args.context)
    for line in diff:
        if line.startswith("+"): print(f"\033[32m{line}\033[0m", end="")
        elif line.startswith("-"): print(f"\033[31m{line}\033[0m", end="")
        elif line.startswith("@@"): print(f"\033[36m{line}\033[0m", end="")
        else: print(line, end="")


def cmd_side(args):
    with open(args.file1) as f: a = f.readlines()
    with open(args.file2) as f: b = f.readlines()
    w = args.width // 2 - 2
    sm = difflib.SequenceMatcher(None, a, b)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                left = a[i].rstrip()[:w]
                print(f"  {left:{w}s}  =  {left}")
        elif tag == "replace":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                left = a[i].rstrip()[:w]
                right = b[j].rstrip()[:w]
                print(f"  \033[31m{left:{w}s}\033[0m  |  \033[32m{right}\033[0m")
        elif tag == "delete":
            for i in range(i1, i2):
                left = a[i].rstrip()[:w]
                print(f"  \033[31m{left:{w}s}\033[0m  <")
        elif tag == "insert":
            for j in range(j1, j2):
                right = b[j].rstrip()[:w]
                print(f"  {'':{w}s}  >  \033[32m{right}\033[0m")


def cmd_stats(args):
    with open(args.file1) as f: a = f.readlines()
    with open(args.file2) as f: b = f.readlines()
    sm = difflib.SequenceMatcher(None, a, b)
    added, removed, changed = 0, 0, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert": added += j2 - j1
        elif tag == "delete": removed += i2 - i1
        elif tag == "replace": changed += max(i2 - i1, j2 - j1)
    ratio = sm.ratio()
    print(f"  {args.file1} vs {args.file2}")
    print(f"  Added:    +{added} lines")
    print(f"  Removed:  -{removed} lines")
    print(f"  Changed:  ~{changed} lines")
    print(f"  Similarity: {ratio*100:.1f}%")


def main():
    p = argparse.ArgumentParser(prog="difftool", description="Diff viewer with color")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("unified", aliases=["u"], help="Unified diff")
    s.add_argument("file1"); s.add_argument("file2"); s.add_argument("-c", "--context", type=int, default=3)
    s = sub.add_parser("side", aliases=["s"], help="Side-by-side")
    s.add_argument("file1"); s.add_argument("file2"); s.add_argument("-w", "--width", type=int, default=120)
    s = sub.add_parser("stats", help="Diff statistics")
    s.add_argument("file1"); s.add_argument("file2")
    args = p.parse_args()
    if not args.cmd: p.print_help(); return 1
    cmds = {"unified": cmd_unified, "u": cmd_unified, "side": cmd_side, "s": cmd_side, "stats": cmd_stats}
    return cmds[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
