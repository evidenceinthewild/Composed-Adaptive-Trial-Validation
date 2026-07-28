#!/usr/bin/env python3
"""
Port the canonical manuscript abstract and body into the format-specific copies.

Defaults to check mode: it reports what would change and writes nothing.
Pass ``--apply`` to write.

Why this exists
---------------
A LaTeX build that compiles proves valid TeX, not current content. An earlier
ad-hoc port keyed on ``\\begin{abstract}``, which the proceedings copy does not
use (it has ``\\section*{Abstract}``). The resulting exception landed mid-loop,
so that copy silently kept BOTH a stale abstract and a stale body, and the
rebuild afterwards reported the expected page count, the expected image count
and zero undefined references. Nothing in the build output revealed it.

Guarantees
----------
* Every manuscript named in the manifest must exist, or nothing happens.
* Each transformation declares how many times it must match; any other count
  aborts the whole run. Zero matches and multiple matches both fail, so a
  document that changed shape cannot be ported silently.
* All outputs are staged and validated in memory before any destination is
  written, so an exception cannot leave a partially ported set.
* Writes go to a temp file in the destination directory and are then moved
  into place.

Usage
-----
    python3 tools/release/port_manuscript.py --manifest path/to/copies.toml
    python3 tools/release/port_manuscript.py --manifest path/to/copies.toml --apply
"""
import argparse
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest as mf  # noqa: E402

BODY_MARK = "\\section{Introduction}"


class PortError(RuntimeError):
    pass


def require(cond, msg):
    if not cond:
        raise PortError(msg)


def split_abstract(text, style):
    """Return (head, abstract_body, tail) for either abstract style."""
    if style == "env":
        b, e = "\\begin{abstract}", "\\end{abstract}"
        require(b in text and e in text, "abstract environment not found")
        i, j = text.index(b) + len(b), text.index(e)
        return text[:i], text[i:j], text[j:]
    h = "\\section*{Abstract}"
    require(h in text, "\\section*{Abstract} not found")
    i = text.index(h) + len(h)
    m = re.search(r"\n%\s*─|\n\\section\{", text[i:])
    require(m is not None, "end of the \\section*{Abstract} block not found")
    j = i + m.start()
    return text[:i], text[i:j], text[j:]


def transform(body, canon_prefix, figpfx, bib, schematic, counts):
    """Apply the permitted per-copy differences, asserting exact match counts."""
    n = body.count(canon_prefix)
    require(n == counts["figure_prefix"],
            f"figure prefix matched {n}x, expected {counts['figure_prefix']}")
    out = body.replace(canon_prefix, figpfx)

    token = "{%s}" % schematic
    n = out.count(token)
    require(n == counts["schematic_path"],
            f"schematic path matched {n}x, expected {counts['schematic_path']}")
    out = out.replace(token, "{%s%s}" % (figpfx, schematic))

    n = len(re.findall(r"\\bibliography\{[^}]*\}", out))
    require(n == counts["bibliography"],
            f"bibliography matched {n}x, expected {counts['bibliography']}")
    out = re.sub(r"\\bibliography\{[^}]*\}", "\\\\bibliography{%s}" % bib, out)
    return out


def build_staged(m):
    """Return {abs_path: new_text} for every non-canonical copy, or raise."""
    manuscripts, canon = m.manuscripts()
    counts = m.table("transformations")
    for k in ("figure_prefix", "schematic_path", "bibliography"):
        require(k in counts, f"[transformations] is missing {k}")
    schematic = m.table("schematic")["filename"]

    paths = {x["name"]: m.abs(x["tex"]) for x in manuscripts}
    missing = [n for n, p in paths.items() if not os.path.exists(p)]
    require(not missing, "missing manuscript source(s): " + ", ".join(sorted(missing)))

    src = mf.read_text(paths[canon["name"]])
    _, canon_abs, _ = split_abstract(src, canon["abstract"])
    require(BODY_MARK in src, "canonical body marker not found")
    canon_body = src[src.index(BODY_MARK):]

    staged = {}
    for entry in manuscripts:
        if entry.get("canonical"):
            continue
        path = paths[entry["name"]]
        try:
            cur = mf.read_text(path)
            head, _, tail = split_abstract(cur, entry["abstract"])
            require(BODY_MARK in tail, "body marker not found after the abstract")
            new_abs = canon_abs if entry["abstract"] == "env" else \
                "\n\n" + canon_abs.replace("\\noindent\n", "").strip() + "\n"
            new_body = transform(canon_body, canon["figure_prefix"],
                                 entry["figure_prefix"], entry["bibliography"],
                                 schematic, counts)
            staged[path] = head + new_abs + tail[:tail.index(BODY_MARK)] + new_body
        except PortError as e:
            raise PortError(f"{entry['name']} ({entry['tex']}): {e}") from None

    expected = len(manuscripts) - 1
    require(len(staged) == expected,
            f"staged {len(staged)} of {expected} copies")
    return staged


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    mf.add_common_args(ap)
    ap.add_argument("--apply", action="store_true",
                    help="write the ported copies (default: check only)")
    args = ap.parse_args(argv)

    try:
        m = mf.load(args.manifest, args.workspace)
        staged = build_staged(m)
    except (PortError, mf.ManifestError) as e:
        print(f"! PORT ABORTED — no file written: {e}")
        return 2

    changed = []
    for path, text in staged.items():
        cur = mf.read_text(path)
        rel = os.path.relpath(path, m.workspace)
        if cur == text:
            print(f"  up to date  {rel}")
        else:
            changed.append(rel)
            print(f"  {'WOULD CHANGE' if not args.apply else 'updated     '}  {rel}")

    if args.apply:
        for path, text in staged.items():
            d = os.path.dirname(path)
            fd, tmp = tempfile.mkstemp(dir=d, suffix=".tex")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
            shutil.move(tmp, path)
        print(f"  applied to {len(staged)} copies")
        return 0

    if changed:
        print(f"  {len(changed)} copy/copies would change — re-run with --apply")
        return 1
    print(f"  all {len(staged)} copies already match the canonical source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
