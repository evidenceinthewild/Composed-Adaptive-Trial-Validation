#!/usr/bin/env python3
"""
Read-only release acceptance check.

This tool never writes. It asserts the publication-critical invariants of the
release, all of which have been violated at least once in this project's
history:

  1. RETRACTED CONTENT   No withdrawn claim or number survives in the extracted
                         text of any container -- PPTX slides and notes, DOCX,
                         TeX, QMD, BIB, MD, rendered HTML and PDF text.
  2. FIGURE HASHES       Every consumer's copy of each rendered figure is
                         byte-identical to the current render.
  3. SCHEMATIC           The hand-built schematic matches across consumers.
                         Its CONTENT is not machine-checkable: a stale
                         schematic once contradicted the corrected manuscript
                         in four places and passed every text sweep, because
                         text baked into a raster is invisible to a regex.
  4. DECK CHARTS         Charts pasted into the deck match the current render.
                         A stale one shipped with a retracted axis label.
  5. BUILD INTEGRITY     Each PDF embeds the expected number of images. A
                         LaTeX run that cannot find a figure still exits 0 and
                         still emits a PDF.
  6. CROSS-COPY          All manuscript copies carry identical scientific
                         content, modulo the permitted per-copy differences.
                         A copy once kept a stale abstract AND body through a
                         build that reported every expected number.

Every path comes from the manifest; nothing is resolved relative to this file.

Usage
-----
    python3 tools/release/check_release.py --manifest path/to/copies.toml

Exit status 0 = release ready, 1 = blockers found.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest as mf  # noqa: E402

BODY_MARK = "\\section{Introduction}"


class ExtractionError(RuntimeError):
    """A container could not be read.

    Extraction failure is FATAL, never warning-level. A file the sweep cannot
    open is a file whose contents were never checked, which is
    indistinguishable from a file that passed -- the failure mode this whole
    tool exists to prevent.
    """


def rule(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def md5(b):
    return hashlib.md5(b).hexdigest()


# ── 1. retracted content ────────────────────────────────────────────────────
def _pptx_text(path):
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if re.match(r"ppt/(slides|notesSlides)/[^/]+\.xml$", n):
                xml = z.read(n).decode("utf-8", "ignore")
                out.append((n, "".join(re.findall(r"<a:t>(.*?)</a:t>", xml, re.S))))
    return out


def _docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    return [("", "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml, re.S)))]


def _plain_text(path):
    t = mf.read_text(path, errors="ignore")
    if path.endswith(".html"):
        t = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
        t = re.sub(r"data:[^\"')\s]{200,}", " ", t)
        t = re.sub(r"<[^>]+>", " ", t)
    return [("", t)]


def _pdf_text(path):
    try:
        r = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True)
    except FileNotFoundError as e:
        raise ExtractionError("pdftotext is not installed") from e
    if r.returncode != 0:
        raise ExtractionError(
            f"pdftotext exited {r.returncode}: {r.stderr.strip()[:120]}")
    return [("", r.stdout)]


def sweep(m):
    rule("RETRACTED CONTENT SWEEP")
    scope = m.table("scope")
    release = tuple(scope.get("release", []))
    skip_dirs = set(scope.get("skip_dirs", []))
    allow = scope.get("allow", [])
    window = int(scope.get("allow_window", 320))
    pats = [(p["pattern"], p["label"]) for p in m.array("retracted")]

    items, unreadable = [], []
    for dirpath, dirnames, files in os.walk(m.workspace):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for f in files:
            # Office owner/lock files (~$name.docx) appear while a document is
            # open. They are not documents -- they hold no content and are not
            # valid OOXML -- so treating them as unreadable containers would
            # block every run made while a file happens to be open in Word.
            if f.startswith("~$"):
                continue
            p, rel = os.path.join(dirpath, f), os.path.relpath(
                os.path.join(dirpath, f), m.workspace)
            try:
                if f.endswith(".pptx"):
                    items += [(rel + "::" + a, b) for a, b in _pptx_text(p)]
                elif f.endswith(".docx"):
                    items += [(rel, b) for _, b in _docx_text(p)]
                elif f.endswith((".tex", ".qmd", ".bib", ".md", ".html", ".Rmd")):
                    items += [(rel, b) for _, b in _plain_text(p)]
                elif f.endswith(".pdf"):
                    items += [(rel, b) for _, b in _pdf_text(p)]
            except Exception as e:
                unreadable.append((rel, f"{type(e).__name__}: {e}"))

    hits, other = [], []
    for name, text in items:
        flat = re.sub(r"\s+", " ", text)
        for pat, label in pats:
            for mt in re.finditer(pat, flat, re.I):
                ctx = flat[max(0, mt.start() - window):mt.start() + window]
                if any(a in ctx for a in allow):
                    continue
                rec = (name, label, flat[max(0, mt.start() - 60):mt.start() + 80])
                base = name.split("::")[0]
                (hits if any(base == r or base.startswith(r) for r in release)
                 else other).append(rec)

    for rel, why in unreadable:
        print(f"  UNREADABLE  {rel}\n              {why}")
    for n, l, c in hits:
        print(f"  BLOCKER  {n}\n           [{l}]  ...{c.strip()}...")
    if not hits and not unreadable:
        print("  RELEASE SET clean — no retracted phrases or numbers")
    if other:
        seen = set()
        print("\n  --- outside the release set (does not block, but is stale) ---")
        for n, l, _ in other:
            if n not in seen:
                seen.add(n)
                print(f"    {n}  [{l}]")
    if unreadable:
        print(f"  {len(unreadable)} container(s) could not be read — "
              f"their contents were never checked")
    return len(hits) + len(unreadable)


# ── 2/3. figure hashes ──────────────────────────────────────────────────────
def figures(m):
    rule("FIGURE HASH CONSISTENCY")
    fig = m.table("figures")
    src = m.abs(fig["source"])
    if not os.path.isdir(src):
        print("  ! source figure directory not found — has the render been run?")
        return 1
    consumers = fig["consumers"]
    bad = 0
    for f in sorted(x for x in os.listdir(src) if x.endswith(".png")):
        h = md5(mf.read_bytes(os.path.join(src, f)))
        row = [f"  {f:<26} {h[:8]}"]
        for c in consumers:
            p = os.path.join(m.abs(c), f)
            if not os.path.exists(p):
                row.append(f"{c.split('/')[0]}:MISSING"); bad += 1
            elif md5(mf.read_bytes(p)) != h:
                row.append(f"{c.split('/')[0]}:STALE"); bad += 1
            else:
                row.append("ok")
        print("  ".join(row))
    print("  all consumers match source" if bad == 0
          else f"  {bad} stale/missing figure copies")
    return bad


def schematic(m):
    rule("SCHEMATIC (raster — not text-swept)")
    sc = m.table("schematic")
    name, consumers = sc["filename"], sc["consumers"]
    ref = m.abs(os.path.join(consumers[0], name))
    if not os.path.exists(ref):
        print(f"  ! {name} missing at {consumers[0]}")
        return 1
    h, bad = md5(mf.read_bytes(ref)), 0
    for c in consumers[1:]:
        p = os.path.join(m.abs(c), name)
        if not os.path.exists(p):
            print(f"  MISSING  {c}/{name}"); bad += 1
        elif md5(mf.read_bytes(p)) != h:
            print(f"  STALE    {c}/{name}"); bad += 1
    print(f"  {name} {h[:8]} — all {len(consumers)} copies match" if bad == 0
          else f"  {bad} bad copies")
    print("  NOTE: hash equality only. Figure content is not machine-checkable —")
    print("        re-read the figure whenever the manuscript's claims change.")
    return bad


# ── 4. deck charts ──────────────────────────────────────────────────────────
def deck_images(m):
    rule("DECK CHART IMAGES (raster — not text-swept)")
    d = m.table("deck")
    path, floor = m.abs(d["path"]), int(d.get("min_chart_bytes", 50000))
    src = m.abs(m.table("figures")["source"])
    if not os.path.exists(path):
        print(f"  ! deck not found: {d['path']}")
        return 1
    if not os.path.isdir(src):
        print("  ! no rendered figures to compare against")
        return 1
    cur = {md5(mf.read_bytes(os.path.join(src, f))): f
           for f in os.listdir(src) if f.endswith(".png")}
    # Presentation-only variants of a rendered figure (no title, legend inside,
    # larger type) are legitimate deck charts but are not produced by the R
    # render. They must be DECLARED in the manifest, so an undeclared or stale
    # chart still fails.
    for extra in d.get("extra_chart_dirs", []):
        ed = m.abs(extra)
        if not os.path.isdir(ed):
            print(f"  ! declared chart dir missing: {extra}")
            return 1
        for f in sorted(os.listdir(ed)):
            if f.endswith(".png"):
                cur.setdefault(md5(mf.read_bytes(os.path.join(ed, f))),
                               f"{extra}/{f}")
    bad = 0
    with zipfile.ZipFile(path) as z:
        for n in sorted(z.namelist()):
            if not re.match(r"ppt/media/.+\.png$", n):
                continue
            blob = z.read(n)
            if len(blob) < floor:
                continue
            h = md5(blob)
            if h in cur:
                print(f"  ok     {os.path.basename(n)} = {cur[h]}")
            else:
                print(f"  STALE  {os.path.basename(n)} matches no figure in the "
                      f"current render ({h[:8]})")
                bad += 1
    print("  every deck chart matches the current render" if bad == 0
          else f"  {bad} stale deck chart(s)")
    return bad


# ── 5. build integrity ──────────────────────────────────────────────────────
def builds(m):
    rule("PDF BUILD INTEGRITY")
    expected = int(m.table("build")["expected_images"])
    manuscripts, _ = m.manuscripts()
    bad = 0
    for entry in manuscripts:
        if "pdf" not in entry:
            continue
        pdf = m.abs(entry["pdf"])
        if not os.path.exists(pdf):
            print(f"  MISSING  {entry['pdf']}"); bad += 1; continue
        try:
            out = subprocess.run(["pdfimages", "-list", pdf],
                                 capture_output=True, text=True).stdout
            n = max(0, len(out.strip().split("\n")) - 2)
        except Exception:
            n = -1
        miss = 0
        log = m.abs(entry["log"]) if "log" in entry else None
        if log and os.path.exists(log):
            miss = mf.read_text(log, errors="ignore").lower().count("not found")
        ok = (n == expected and miss == 0)
        print(f"  {'ok    ' if ok else 'BROKEN'} {entry['pdf']} — {n} images, "
              f"{miss} missing-file errors")
        if not ok:
            bad += 1
    print("  every build embedded all figures" if bad == 0
          else f"  {bad} build(s) missing figures")
    return bad


# ── 6. cross-copy consistency ───────────────────────────────────────────────
def normalise(t, prefixes):
    for p in prefixes:
        if p:
            t = t.replace(p, "")
    t = re.sub(r"\\bibliography\{[^}]*\}", r"\\bibliography{BIB}", t)
    t = t.replace("\\noindent", " ")
    t = re.sub(r"(?m)^\s*%.*$", "", t)
    return re.sub(r"\s+", " ", t).strip()


def extract_abstract(text, style):
    if style == "env":
        b, e = "\\begin{abstract}", "\\end{abstract}"
        if b not in text or e not in text:
            return None
        return text[text.index(b) + len(b):text.index(e)]
    h = "\\section*{Abstract}"
    if h not in text:
        return None
    i = text.index(h) + len(h)
    mt = re.search(r"\n%\s*─|\n\\section\{", text[i:])
    return text[i:i + mt.start()] if mt else None


def extract_sections(text, prefixes):
    if BODY_MARK not in text:
        return None
    body = text[text.index(BODY_MARK):]
    parts = re.split(r"(\\(?:sub)?section\*?\{[^}]*\})", body)
    out, name = [], None
    for chunk in parts:
        if re.fullmatch(r"\\(?:sub)?section\*?\{[^}]*\}", chunk or ""):
            name = re.sub(r"\\(?:sub)?section\*?\{|\}$", "", chunk)
        elif name is not None:
            out.append((name, normalise(chunk, prefixes)))
    return out


def copies(m):
    rule("CROSS-COPY CONTENT CONSISTENCY")
    manuscripts, canon = m.manuscripts()
    prefixes = sorted((e["figure_prefix"] for e in manuscripts), key=len, reverse=True)

    missing = [e["name"] for e in manuscripts if not os.path.exists(m.abs(e["tex"]))]
    if missing:
        print("  MISSING source file(s): " + ", ".join(missing))
        return 1

    docs = {}
    for e in manuscripts:
        t = open(m.abs(e["tex"]), encoding="utf-8").read()
        a, secs = extract_abstract(t, e["abstract"]), extract_sections(t, prefixes)
        if a is None or secs is None:
            print(f"  BROKEN  {e['name']}: could not extract "
                  f"{'abstract' if a is None else 'sections'}")
            return 1
        docs[e["name"]] = (normalise(a, prefixes), secs)

    ref = canon["name"]
    ra, rs = docs[ref]
    bad = 0
    for e in manuscripts:
        if e["name"] == ref:
            continue
        a, secs = docs[e["name"]]
        if a != ra:
            print(f"  DIFFERS  {e['name']}: ABSTRACT does not match {ref}")
            bad += 1
            continue
        if [x[0] for x in secs] != [x[0] for x in rs]:
            only = set(x[0] for x in secs) ^ set(x[0] for x in rs)
            print(f"  DIFFERS  {e['name']}: section list differs — {sorted(only)[:3]}")
            bad += 1
            continue
        first = next(((n) for (n, b), (_, rb) in zip(secs, rs) if b != rb), None)
        if first:
            print(f'  DIFFERS  {e["name"]}: first differing section — "{first}"')
            bad += 1

    for e in manuscripts:
        a, secs = docs[e["name"]]
        h = md5((a + "".join(b for _, b in secs)).encode())
        print(f"  {e['name']:12} {h[:12]}  {len(secs)} sections")
    print("  all copies carry identical scientific content" if bad == 0
          else f"  {bad} copy/copies out of sync — run tools/release/port_manuscript.py")
    return bad


CHECKS = [sweep, figures, schematic, deck_images, builds, copies]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only release acceptance check.")
    mf.add_common_args(ap)
    ap.add_argument("--only", default=None,
                    help="run one check by name (%s)" %
                         ",".join(c.__name__ for c in CHECKS))
    args = ap.parse_args(argv)
    m = mf.load(args.manifest, args.workspace)

    checks = CHECKS
    if args.only:
        checks = [c for c in CHECKS if c.__name__ == args.only]
        if not checks:
            sys.exit(f"! no such check: {args.only}")

    n = sum(c(m) for c in checks)
    print()
    print("=" * 72)
    print("RELEASE READY" if n == 0 else f"NOT READY — {n} blocker(s)")
    print("=" * 72)
    return 0 if n == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except mf.ManifestError as e:
        sys.exit(f"! MANIFEST ERROR: {e}")
