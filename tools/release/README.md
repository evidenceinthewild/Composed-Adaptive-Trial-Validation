# Release tools

Two tools and a manifest. Both take `--manifest PATH`; every path they touch
comes from that manifest, resolved against a workspace root that is either
`--workspace` or the manifest's own directory. Nothing resolves relative to the
scripts, and no absolute user-specific path is stored.

```bash
cp tools/release/copies.example.toml ../copies.toml   # then edit for your layout

python3 tools/release/check_release.py   --manifest ../copies.toml   # read-only
python3 tools/release/port_manuscript.py --manifest ../copies.toml   # check mode
python3 tools/release/port_manuscript.py --manifest ../copies.toml --apply
python3 tools/release/test_release_tools.py                          # 25 tests
```

`check_release.py` never writes. `port_manuscript.py` defaults to check mode and
requires `--apply`.

## What these enforce, and why

Each invariant corresponds to a failure that actually reached a built artifact
in this project. A LaTeX build that compiles proves valid TeX, not current
content; every one of these passed a clean-looking build.

| Invariant | The failure it prevents |
|---|---|
| Retracted content | Withdrawn claims surviving in slides, notes, script, TeX or rendered output |
| Figure hashes | A consumer directory holding a pre-correction render |
| Schematic | A diagram contradicting the corrected manuscript in four places — invisible to a text sweep, because its text is raster |
| Deck charts | Slide 8 shipping a chart whose axis label had been retracted |
| Build integrity | A missing figure: `pdflatex` prints a warning, emits a PDF and exits 0 |
| Cross-copy | A copy keeping a stale abstract *and* body through a build reporting every expected number |

**Extraction failure is fatal.** A container the sweep cannot open is a
container whose contents were never checked, which is indistinguishable from
one that passed. Unreadable files are blockers, never warnings.

**Transformations declare their match counts.** Zero matches and multiple
matches both abort. A document that changed shape cannot be ported silently.

**Nothing is written until everything validates.** All outputs are staged in
memory first, so an exception cannot leave a partially ported set.

## Known limits

- The schematic is checked by hash only. Its *content* is not machine-checkable
  — re-read it whenever the manuscript's claims change.
- `manifest.py` falls back to a documented TOML subset parser on Python < 3.11
  (no `tomllib`). This is acceptable while the schema stays narrow and tested.
  If the schema grows, switch to JSON rather than maintaining a parser.

## Deferred: canonical `\input` body

The real fix for cross-copy drift is one canonical abstract and body `\input`
by each format-specific wrapper, with a flattened copy generated for arXiv.
That removes the duplication these tools currently police.

**Deferred until after the JSM 2026 submission.** The cross-copy assertion
addresses the immediate risk; restructuring the document architecture before
submission would introduce more release risk than it removes. When it lands,
content synchronisation retires from `port_manuscript.py` and
`check_release.py` narrows to verifying generated submission artifacts. The
manifest carries over unchanged — it is already the right seam.
