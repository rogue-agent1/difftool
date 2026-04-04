#!/usr/bin/env python3
"""difftool - structural diff for files, directories, strings with colorized output."""

import argparse, sys, os, difflib, hashlib, stat, time

R = "\033[31m"
G = "\033[32m"
Y = "\033[33m"
C = "\033[36m"
D = "\033[2m"
B = "\033[1m"
RST = "\033[0m"

def file_hash(path, algo="sha256"):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def cmd_files(args):
    """Diff two files with unified/side-by-side output."""
    with open(args.file1, errors="replace") as f:
        lines1 = f.readlines()
    with open(args.file2, errors="replace") as f:
        lines2 = f.readlines()

    if args.side:
        _side_by_side(lines1, lines2, args.file1, args.file2, args.width)
    else:
        ctx = args.context
        diff = difflib.unified_diff(lines1, lines2, fromfile=args.file1, tofile=args.file2, n=ctx)
        added = removed = 0
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                print(f"{B}{line.rstrip()}{RST}")
            elif line.startswith("@@"):
                print(f"{C}{line.rstrip()}{RST}")
            elif line.startswith("+"):
                print(f"{G}{line.rstrip()}{RST}")
                added += 1
            elif line.startswith("-"):
                print(f"{R}{line.rstrip()}{RST}")
                removed += 1
            else:
                print(line.rstrip())
        print(f"\n  {G}+{added}{RST} {R}-{removed}{RST} lines changed")

def _side_by_side(lines1, lines2, name1, name2, width):
    half = (width - 3) // 2
    print(f"{B}{name1:<{half}} │ {name2}{RST}")
    print("─" * half + "─┼─" + "─" * half)
    sm = difflib.SequenceMatcher(None, lines1, lines2)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                l = lines1[i1 + k].rstrip()[:half]
                r = lines2[j1 + k].rstrip()[:half]
                print(f"{D}{l:<{half}}{RST} │ {D}{r}{RST}")
        elif tag == "replace":
            mx = max(i2 - i1, j2 - j1)
            for k in range(mx):
                l = lines1[i1 + k].rstrip()[:half] if i1 + k < i2 else ""
                r = lines2[j1 + k].rstrip()[:half] if j1 + k < j2 else ""
                print(f"{R}{l:<{half}}{RST} │ {G}{r}{RST}")
        elif tag == "delete":
            for k in range(i2 - i1):
                l = lines1[i1 + k].rstrip()[:half]
                print(f"{R}{l:<{half}}{RST} │")
        elif tag == "insert":
            for k in range(j2 - j1):
                r = lines2[j1 + k].rstrip()[:half]
                print(f"{'':>{half}} │ {G}{r}{RST}")

def cmd_dirs(args):
    """Diff two directories."""
    dir1, dir2 = args.dir1, args.dir2

    def scan(d):
        files = {}
        for root, dirs, fnames in os.walk(d):
            dirs[:] = sorted(x for x in dirs if not x.startswith("."))
            for f in sorted(fnames):
                if f.startswith("."):
                    continue
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, d)
                try:
                    st = os.stat(fp)
                    files[rel] = {"size": st.st_size, "mtime": st.st_mtime}
                except OSError:
                    pass
        return files

    f1 = scan(dir1)
    f2 = scan(dir2)
    all_files = sorted(set(f1) | set(f2))

    only1, only2, differ, same = [], [], [], []
    for f in all_files:
        if f not in f2:
            only1.append(f)
        elif f not in f1:
            only2.append(f)
        elif f1[f]["size"] != f2[f]["size"]:
            differ.append(f)
        elif args.checksum:
            h1 = file_hash(os.path.join(dir1, f))
            h2 = file_hash(os.path.join(dir2, f))
            if h1 != h2:
                differ.append(f)
            else:
                same.append(f)
        else:
            same.append(f)

    print(f"\n  Directory diff: {dir1} ↔ {dir2}")
    print("  " + "─" * 50)

    if only1:
        print(f"\n  {R}Only in {dir1}:{RST}")
        for f in only1:
            print(f"    {R}- {f}{RST}")
    if only2:
        print(f"\n  {G}Only in {dir2}:{RST}")
        for f in only2:
            print(f"    {G}+ {f}{RST}")
    if differ:
        print(f"\n  {Y}Different:{RST}")
        for f in differ:
            s1 = f1[f]["size"]
            s2 = f2[f]["size"]
            delta = s2 - s1
            sign = "+" if delta >= 0 else ""
            print(f"    {Y}~ {f}  ({s1}→{s2}, {sign}{delta}){RST}")

    print(f"\n  {len(only1)} only-left, {len(only2)} only-right, {len(differ)} different, {len(same)} identical")
    print(f"  Total: {len(all_files)} files compared\n")

def cmd_strings(args):
    """Diff two strings character-by-character."""
    s1, s2 = args.string1, args.string2
    sm = difflib.SequenceMatcher(None, s1, s2)
    ratio = sm.ratio()

    out1, out2 = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out1.append(s1[i1:i2])
            out2.append(s2[j1:j2])
        elif tag == "replace":
            out1.append(f"{R}{s1[i1:i2]}{RST}")
            out2.append(f"{G}{s2[j1:j2]}{RST}")
        elif tag == "delete":
            out1.append(f"{R}{s1[i1:i2]}{RST}")
        elif tag == "insert":
            out2.append(f"{G}{s2[j1:j2]}{RST}")

    print(f"\n  String 1: {''.join(out1)}")
    print(f"  String 2: {''.join(out2)}")
    print(f"  Similarity: {ratio*100:.1f}%")
    print(f"  Lengths: {len(s1)} → {len(s2)} ({'+' if len(s2)>=len(s1) else ''}{len(s2)-len(s1)})\n")

def cmd_stat(args):
    """Show diff statistics between two files."""
    with open(args.file1, errors="replace") as f:
        lines1 = f.readlines()
    with open(args.file2, errors="replace") as f:
        lines2 = f.readlines()

    sm = difflib.SequenceMatcher(None, lines1, lines2)
    added = removed = changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "replace":
            changed += max(i2 - i1, j2 - j1)

    ratio = sm.ratio()
    print(f"\n  Diff Stats: {args.file1} ↔ {args.file2}")
    print("  " + "─" * 40)
    print(f"  Lines (old):   {len(lines1)}")
    print(f"  Lines (new):   {len(lines2)}")
    print(f"  {G}Added:         +{added}{RST}")
    print(f"  {R}Removed:       -{removed}{RST}")
    print(f"  {Y}Changed:       ~{changed}{RST}")
    print(f"  Similarity:    {ratio*100:.1f}%")

    h1 = file_hash(args.file1)
    h2 = file_hash(args.file2)
    print(f"  SHA256 match:  {'Yes ✅' if h1 == h2 else 'No'}")
    print()

def main():
    p = argparse.ArgumentParser(description="Structural diff tool")
    sp = p.add_subparsers(dest="cmd")

    f = sp.add_parser("files", help="Diff two files")
    f.add_argument("file1")
    f.add_argument("file2")
    f.add_argument("-c", "--context", type=int, default=3)
    f.add_argument("-s", "--side", action="store_true", help="Side-by-side")
    f.add_argument("-w", "--width", type=int, default=120)
    f.set_defaults(func=cmd_files)

    d = sp.add_parser("dirs", help="Diff two directories")
    d.add_argument("dir1")
    d.add_argument("dir2")
    d.add_argument("--checksum", action="store_true", help="Compare checksums")
    d.set_defaults(func=cmd_dirs)

    s = sp.add_parser("strings", help="Diff two strings")
    s.add_argument("string1")
    s.add_argument("string2")
    s.set_defaults(func=cmd_strings)

    st = sp.add_parser("stat", help="Diff statistics")
    st.add_argument("file1")
    st.add_argument("file2")
    st.set_defaults(func=cmd_stat)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        sys.exit(1)
    args.func(args)

if __name__ == "__main__":
    main()
