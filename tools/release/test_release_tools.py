#!/usr/bin/env python3
"""
Regression tests for the release tools. Standard library only (unittest).

    python3 tools/release/test_release_tools.py

Every test builds a throwaway fixture workspace in a temp directory, so the
tools are exercised through their real manifest interface with no dependence on
the actual manuscript, and nothing on disk is touched.

The two content regressions reproduced here are the ones that actually reached
a built PDF in this project:

  * a copy keeping a stale ABSTRACT while compiling cleanly;
  * a copy keeping a stale CONCLUSION while compiling cleanly.

Both were invisible to page counts, image counts and undefined-reference
counts, which is why they need a test.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import manifest as mf                     # noqa: E402
import port_manuscript as port            # noqa: E402
import check_release as check             # noqa: E402

CANON_PREFIX = "figs/render/"

ABSTRACT = ("Canonical abstract: the fixed-$\\gamma^*$ difference between the "
            "full design and the ablation reverses sign.")
CONCLUSION = ("Point calibration did not provide uniform Type~I error control "
              "across the composite null.")


def tex(prefix, bib, abstract_style, abstract=ABSTRACT, conclusion=CONCLUSION):
    if abstract_style == "env":
        head = ("\\documentclass{article}\n\\begin{document}\n"
                "\\begin{abstract}\n\\noindent\n" + abstract +
                "\n\\end{abstract}\n\n")
    else:
        head = ("\\documentclass{article}\n\\begin{document}\n"
                "\\section*{Abstract}\n\n" + abstract + "\n\n")
    body = (
        "\\section{Introduction}\nIntro text.\n\n"
        "\\section{Results}\n"
        "\\includegraphics{%scomposite-null-plot-1.png}\n"
        "\\includegraphics{%sdeparture-trend-crossing-1.png}\n"
        "\\includegraphics{Figure1_Composed_Design.png}\n\n"
        "\\section{Conclusion}\n%s\n\n"
        "\\bibliography{%s}\n\\end{document}\n" % (prefix, prefix, conclusion, bib)
    )
    return head + body


MANIFEST = """
[build]
expected_images = 3

[transformations]
figure_prefix = 2
schematic_path = 1
bibliography = 1

[figures]
source = "figs/render"
consumers = ["copyA", "copyB"]

[schematic]
filename = "Figure1_Composed_Design.png"
consumers = [".", "copyA"]

[deck]
path = "deck.pptx"

[scope]
release = ["main.tex"]
skip_dirs = [".git"]
allow_window = 100
allow = ["deliberately quoted"]

[[retracted]]
pattern = 'withdrawn claim'
label = "test pattern"

[[manuscript]]
name = "root"
tex = "main.tex"
figure_prefix = "figs/render/"
bibliography = "references_main"
abstract = "env"
canonical = true

[[manuscript]]
name = "copyA"
tex = "copyA/main.tex"
figure_prefix = "figures/"
bibliography = "references"
abstract = "env"
canonical = false

[[manuscript]]
name = "proceedings"
tex = "proceedings/proc.tex"
figure_prefix = ""
bibliography = "references"
abstract = "section"
canonical = false
"""


class Fixture:
    """A throwaway workspace with three manuscript copies, already in sync."""

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="release-fixture-")
        os.makedirs(os.path.join(self.dir, "copyA"))
        os.makedirs(os.path.join(self.dir, "proceedings"))
        self.write("main.tex", tex(CANON_PREFIX, "references_main", "env"))
        self.write("copyA/main.tex", tex("figures/", "references", "env"))
        self.write("proceedings/proc.tex", tex("", "references", "section"))
        self.manifest = os.path.join(self.dir, "copies.toml")
        with open(self.manifest, "w") as fh:
            fh.write(MANIFEST)
        return self

    def __exit__(self, *a):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, rel, text):
        with open(os.path.join(self.dir, rel), "w") as fh:
            fh.write(text)

    def read(self, rel):
        return mf.read_text(os.path.join(self.dir, rel))

    def snapshot(self):
        return {r: self.read(r) for r in
                ("main.tex", "copyA/main.tex", "proceedings/proc.tex")}


def run(fn, *argv):
    """Run a tool's main(), capturing stdout; return (exit_code, output)."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = fn(list(argv))
    except SystemExit as e:
        code = e.code
    return code, buf.getvalue()


# ── manifest ────────────────────────────────────────────────────────────────
class TestManifest(unittest.TestCase):
    def test_subset_parser_matches_expected_shape(self):
        d = mf.parse_toml(MANIFEST)
        self.assertEqual(d["transformations"]["figure_prefix"], 2)
        self.assertEqual(d["figures"]["consumers"], ["copyA", "copyB"])
        self.assertEqual(len(d["manuscript"]), 3)
        self.assertTrue(d["manuscript"][0]["canonical"])
        self.assertFalse(d["manuscript"][1]["canonical"])
        # literal strings keep regex backslashes intact
        self.assertEqual(d["retracted"][0]["pattern"], "withdrawn claim")

    def test_parses_the_shipped_example_manifest(self):
        example = os.path.join(HERE, "copies.example.toml")
        d = mf.parse_toml(mf.read_text(example))
        self.assertEqual(len(d["manuscript"]), 1)
        self.assertTrue(d["manuscript"][0]["canonical"])
        self.assertEqual(d["build"]["expected_images"], 7)
        self.assertTrue(any(r"7\.7\s*" in p["pattern"] for p in d["retracted"]),
                        "regex escapes must survive the literal-string parser")

    def test_conflict_label_pattern_matches_obsolete_variants(self):
        """Anchor departures must not be relabeled as quantified conflict."""
        d = mf.parse_toml(mf.read_text(os.path.join(HERE, "copies.example.toml")))
        pat = next(p["pattern"] for p in d["retracted"]
                   if p["label"] == "conflict label used for anchor departure")
        for s in ("mild conflict", "strong conflict scenario",
                  "moderate conflict"):
            self.assertRegex(s, pat, f"missed: {s}")

    def test_headline_pattern_catches_decimal_and_percentage_forms(self):
        """The same retracted number written two ways must not escape."""
        d = mf.parse_toml(mf.read_text(os.path.join(HERE, "copies.example.toml")))
        pat = next(p["pattern"] for p in d["retracted"]
                   if p["label"] == "obsolete headline T1E")
        for s in ("T1E of 0.0771 under mild conflict",
                  "inflated Type I error to 7.7%",
                  "inflated Type I error to 7.7 percent"):
            self.assertRegex(s, pat, f"missed: {s}")

    def test_prohibition_context_is_allow_listed(self):
        """"Do not say X" must not be reported as an assertion of X."""
        with Fixture() as f:
            f.write("copies.toml", MANIFEST.replace(
                'allow = ["deliberately quoted"]',
                'allow = ["deliberately quoted", "Do not say"]'))
            f.write("main.tex", tex(CANON_PREFIX, "references_main", "env",
                                    conclusion="Do not say: this is a withdrawn claim."))
            code, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertEqual(code, 0, out)
            self.assertNotIn("BLOCKER", out)

    def test_allow_region_scopes_a_whole_passage(self):
        """A revision-summary table quotes withdrawn claims on purpose."""
        with Fixture() as f:
            f.write("copies.toml", MANIFEST.replace(
                'allow = ["deliberately quoted"]',
                'allow = ["deliberately quoted"]\n'
                'allow_regions = ["REVISION SUMMARY", "END SUMMARY"]'))
            filler = "x " * 400          # far beyond any proximity window
            f.write("main.tex", tex(CANON_PREFIX, "references_main", "env",
                                    conclusion="REVISION SUMMARY " + filler +
                                    "a withdrawn claim " + filler + "END SUMMARY"))
            code, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertEqual(code, 0, "inside the region must be exempt: " + out)

            # the same phrase OUTSIDE the region must still fail
            f.write("main.tex", tex(CANON_PREFIX, "references_main", "env",
                                    conclusion="REVISION SUMMARY END SUMMARY "
                                    + filler + "a withdrawn claim"))
            code, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertEqual(code, 1, "outside the region must still be caught")
            self.assertIn("BLOCKER", out)

    def test_missing_manifest_is_an_error(self):
        with self.assertRaises(mf.ManifestError):
            mf.load(os.path.join(HERE, "does-not-exist.toml"))

    def test_requires_exactly_one_canonical(self):
        with Fixture() as f:
            # make copyA canonical too, so two entries claim it
            f.write("copies.toml", MANIFEST.replace(
                'canonical = false', 'canonical = true', 1))
            with self.assertRaises(mf.ManifestError):
                mf.load(f.manifest).manuscripts()

    def test_rejects_unknown_abstract_style(self):
        with Fixture() as f:
            f.write("copies.toml", MANIFEST.replace(
                'abstract = "section"', 'abstract = "wrapper"'))
            with self.assertRaises(mf.ManifestError):
                mf.load(f.manifest).manuscripts()


# ── porting ─────────────────────────────────────────────────────────────────
class TestPort(unittest.TestCase):
    def test_defaults_to_check_mode_and_writes_nothing(self):
        with Fixture() as f:
            f.write("copyA/main.tex", tex("figures/", "references", "env",
                                          conclusion="STALE CONCLUSION."))
            before = f.snapshot()
            code, out = run(port.main, "--manifest", f.manifest)
            self.assertEqual(code, 1, "drifted copy must be reported")
            self.assertIn("WOULD CHANGE", out)
            self.assertEqual(f.snapshot(), before, "check mode must not write")

    def test_apply_writes_and_converges(self):
        with Fixture() as f:
            f.write("copyA/main.tex", tex("figures/", "references", "env",
                                          conclusion="STALE CONCLUSION."))
            code, _ = run(port.main, "--manifest", f.manifest, "--apply")
            self.assertEqual(code, 0)
            self.assertIn(CONCLUSION, f.read("copyA/main.tex"))
            self.assertNotIn("STALE CONCLUSION", f.read("copyA/main.tex"))
            # per-copy differences must be preserved, not flattened
            self.assertIn("{figures/composite-null-plot-1.png}", f.read("copyA/main.tex"))
            self.assertIn("\\bibliography{references}", f.read("copyA/main.tex"))
            code, out = run(port.main, "--manifest", f.manifest)
            self.assertEqual(code, 0)
            self.assertIn("already match", out)

    def test_proceedings_abstract_style_is_ported_not_skipped(self):
        """The exact bug: a copy using \\section*{Abstract} was silently skipped."""
        with Fixture() as f:
            f.write("proceedings/proc.tex",
                    tex("", "references", "section", abstract="STALE ABSTRACT.",
                        conclusion="STALE CONCLUSION."))
            run(port.main, "--manifest", f.manifest, "--apply")
            got = f.read("proceedings/proc.tex")
            self.assertIn(ABSTRACT, got)
            self.assertIn(CONCLUSION, got)
            self.assertNotIn("STALE", got)
            self.assertIn("\\section*{Abstract}", got, "wrapper must be preserved")

    def test_wrong_expected_count_aborts_writing_nothing(self):
        with Fixture() as f:
            f.write("copies.toml", MANIFEST.replace("figure_prefix = 2",
                                                    "figure_prefix = 99"))
            before = f.snapshot()
            with self.assertRaises(port.PortError):
                port.build_staged(mf.load(f.manifest))
            self.assertEqual(f.snapshot(), before)

    def test_zero_matches_also_aborts(self):
        with Fixture() as f:
            f.write("copies.toml", MANIFEST.replace("bibliography = 1",
                                                    "bibliography = 0"))
            with self.assertRaises(port.PortError):
                port.build_staged(mf.load(f.manifest))

    def test_missing_copy_aborts_before_touching_any_file(self):
        with Fixture() as f:
            os.remove(os.path.join(f.dir, "copyA/main.tex"))
            before = f.read("proceedings/proc.tex")
            with self.assertRaises(port.PortError):
                port.build_staged(mf.load(f.manifest))
            self.assertEqual(f.read("proceedings/proc.tex"), before,
                             "a later copy must not be written when an "
                             "earlier one fails")

    def test_partial_failure_leaves_no_partial_set(self):
        """Second copy is malformed; the first must still be untouched."""
        with Fixture() as f:
            f.write("proceedings/proc.tex", "\\documentclass{article}\nno abstract\n")
            before = f.snapshot()
            code, out = run(port.main, "--manifest", f.manifest, "--apply")
            self.assertEqual(code, 2, "abort must be an exit code, not a traceback")
            self.assertIn("PORT ABORTED", out)
            self.assertEqual(f.snapshot(), before)


# ── cross-copy consistency ──────────────────────────────────────────────────
class TestConsistency(unittest.TestCase):
    def test_sweep_reads_every_container_without_error(self):
        """A swallowed exception in an extractor must not look like a clean sweep."""
        with Fixture() as f:
            _, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertNotIn("could not read", out,
                             "an extractor raised and the sweep hid it")
            self.assertIn("RELEASE SET clean", out)

    def test_sweep_flags_a_retracted_pattern(self):
        with Fixture() as f:
            f.write("main.tex", tex(CANON_PREFIX, "references_main", "env",
                                     conclusion="This is a withdrawn claim."))
            code, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertEqual(code, 1)
            self.assertIn("BLOCKER", out)

    def test_office_lock_files_are_skipped_not_fatal(self):
        """~$name.docx appears while Word has a file open; it is not content."""
        with Fixture() as f:
            f.write("~$main.docx", "not a zip -- Office owner file")
            code, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertEqual(code, 0, "a lock file must not block the release")
            self.assertNotIn("UNREADABLE", out)

    def test_declared_slide_chart_passes_undeclared_fails(self):
        """A presentation variant is legitimate only if the manifest declares it."""
        import zipfile as zf
        with Fixture() as f:
            os.makedirs(os.path.join(f.dir, "figs/render"))
            os.makedirs(os.path.join(f.dir, "slide-figures"))
            png = b"\x89PNG\r\n\x1a\n" + b"R" * 60000      # "rendered"
            slide = b"\x89PNG\r\n\x1a\n" + b"S" * 60000     # slide variant
            rogue = b"\x89PNG\r\n\x1a\n" + b"X" * 60000     # neither
            with open(os.path.join(f.dir, "figs/render/a.png"), "wb") as fh:
                fh.write(png)
            with open(os.path.join(f.dir, "slide-figures/a-slide.png"), "wb") as fh:
                fh.write(slide)

            def deck(payload):
                p = os.path.join(f.dir, "deck.pptx")
                with zf.ZipFile(p, "w") as z:
                    z.writestr("ppt/media/image1.png", payload)

            man = MANIFEST.replace('path = "deck.pptx"',
                                   'path = "deck.pptx"\nextra_chart_dirs = ["slide-figures"]')
            f.write("copies.toml", man)

            deck(slide)
            code, out = run(check.main, "--manifest", f.manifest,
                            "--only", "deck_images")
            self.assertEqual(code, 0, "declared slide chart must pass: " + out)

            deck(rogue)
            code, out = run(check.main, "--manifest", f.manifest,
                            "--only", "deck_images")
            self.assertEqual(code, 1, "undeclared chart must still fail")
            self.assertIn("STALE", out)

    def test_malformed_pptx_is_fatal(self):
        """A container that cannot be opened was never checked -- never warn."""
        with Fixture() as f:
            f.write("broken.pptx", "this is not a zip archive")
            code, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertEqual(code, 1, "unreadable container must fail the run")
            self.assertIn("UNREADABLE", out)
            self.assertIn("broken.pptx", out)

    def test_docx_extraction_survives_tables(self):
        """<w:t[^>]*> also matches <w:tab/> and <w:tc>, corrupting table docs."""
        with Fixture() as f:
            import zipfile as zf
            body = ("<w:document><w:body>"
                    "<w:p><w:r><w:t>before</w:t></w:r></w:p>"
                    "<w:tbl><w:tr><w:tc><w:tcPr><w:tcW w:w=\"0\"/></w:tcPr>"
                    "<w:p><w:r><w:t>a withdrawn claim</w:t></w:r></w:p></w:tc>"
                    "<w:tc><w:p><w:r><w:tab/><w:t>after</w:t></w:r></w:p></w:tc>"
                    "</w:tr></w:tbl></w:body></w:document>")
            p = os.path.join(f.dir, "t.docx")
            with zf.ZipFile(p, "w") as z:
                z.writestr("word/document.xml", body)
            text = check._docx_text(p)[0][1]
            self.assertNotIn("<w:", text, "markup leaked into extracted text")
            self.assertIn("a withdrawn claim", text)
            self.assertIn("after", text)

    def test_malformed_docx_is_fatal(self):
        with Fixture() as f:
            import zipfile
            p = os.path.join(f.dir, "broken.docx")
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("not/the/expected/part.xml", "<x/>")
            code, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertEqual(code, 1)
            self.assertIn("UNREADABLE", out)

    def test_undecodable_pdf_is_fatal(self):
        with Fixture() as f:
            f.write("broken.pdf", "%PDF-1.4 truncated garbage")
            code, out = run(check.main, "--manifest", f.manifest, "--only", "sweep")
            self.assertEqual(code, 1, "pdftotext failure must not be an empty doc")
            self.assertIn("UNREADABLE", out)

    def test_unreadable_permissions_are_fatal(self):
        with Fixture() as f:
            p = os.path.join(f.dir, "locked.tex")
            f.write("locked.tex", "\\section{Introduction}\n")
            os.chmod(p, 0o000)
            try:
                if os.access(p, os.R_OK):
                    self.skipTest("running as root; permissions are not enforced")
                code, out = run(check.main, "--manifest", f.manifest,
                                "--only", "sweep")
                self.assertEqual(code, 1)
                self.assertIn("UNREADABLE", out)
            finally:
                os.chmod(p, 0o644)

    def test_synchronised_copies_pass(self):
        with Fixture() as f:
            code, out = run(check.main, "--manifest", f.manifest, "--only", "copies")
            self.assertEqual(code, 0, out)
            self.assertIn("identical scientific content", out)

    def test_detects_stale_abstract(self):
        with Fixture() as f:
            f.write("proceedings/proc.tex",
                    tex("", "references", "section",
                        abstract="the net effect of composition reverses direction."))
            code, out = run(check.main, "--manifest", f.manifest, "--only", "copies")
            self.assertEqual(code, 1)
            self.assertIn("ABSTRACT does not match", out)

    def test_detects_stale_conclusion_and_names_the_section(self):
        with Fixture() as f:
            f.write("copyA/main.tex",
                    tex("figures/", "references", "env",
                        conclusion="Point calibration did not provide robust control."))
            code, out = run(check.main, "--manifest", f.manifest, "--only", "copies")
            self.assertEqual(code, 1)
            self.assertIn('first differing section — "Conclusion"', out)

    def test_permitted_differences_do_not_trip_the_check(self):
        """Figure prefixes and bibliography stems differ by design."""
        with Fixture() as f:
            a, b = f.read("copyA/main.tex"), f.read("proceedings/proc.tex")
            self.assertNotEqual(a, b, "fixture copies must genuinely differ")
            code, out = run(check.main, "--manifest", f.manifest, "--only", "copies")
            self.assertEqual(code, 0, out)

    def test_reports_hash_per_copy(self):
        with Fixture() as f:
            _, out = run(check.main, "--manifest", f.manifest, "--only", "copies")
            for name in ("root", "copyA", "proceedings"):
                self.assertRegex(out, rf"{name}\s+[0-9a-f]{{12}}\s+\d+ sections")

    def test_missing_source_is_a_blocker_not_a_skip(self):
        with Fixture() as f:
            os.remove(os.path.join(f.dir, "copyA/main.tex"))
            code, out = run(check.main, "--manifest", f.manifest, "--only", "copies")
            self.assertEqual(code, 1)
            self.assertIn("MISSING", out)


# ── the checker must never write ────────────────────────────────────────────
class TestCheckerIsReadOnly(unittest.TestCase):
    def test_no_file_is_modified_by_a_full_run(self):
        with Fixture() as f:
            before = {}
            for root, _, files in os.walk(f.dir):
                for x in files:
                    p = os.path.join(root, x)
                    before[p] = (os.path.getmtime(p), mf.read_bytes(p))
            run(check.main, "--manifest", f.manifest)
            after = {}
            for root, _, files in os.walk(f.dir):
                for x in files:
                    p = os.path.join(root, x)
                    after[p] = (os.path.getmtime(p), mf.read_bytes(p))
            self.assertEqual(set(before), set(after), "no file may be created")
            for p in before:
                self.assertEqual(before[p][1], after[p][1], f"{p} was modified")


if __name__ == "__main__":
    unittest.main(verbosity=2)
