# Producing software environment

The results in this repository were produced under the environment below.
Recorded because the MAP prior is fitted through `RBesT` → `rstan`, and every
operating characteristic in the study conditions on that fitted mixture: a
change in either package can move the prior, and moving the prior moves every
number in the paper.

`simulation/SESSION_INFO.txt` is written by the render and is authoritative;
this table is a summary and may lag it. As of the 14 Aug 2026 render:

| | |
|---|---|
| R | 4.6.1 (2026-06-24) |
| Platform | aarch64-apple-darwin23 |
| OS | macOS Tahoe 26.6.1 |
| RBesT | 1.10-0 |
| rstan | 2.32.7 |
| StanHeaders | 2.32.10 |
| posterior | 1.7.0 |
| ggplot2 | 4.0.3 |
| dplyr | 1.2.1 |
| knitr | 1.51 |
| rmarkdown | 2.31 |

These are the versions that produced the published figures and tables. Earlier
versions are **untested** — in particular `robustify()` has returned
`Beta(1,1)` or `Beta(0.5,0.5)` depending on `n` and the RBesT version, which
would change the fitted mixture and therefore every result.

## What is checked automatically

`simulation/simulation_study.qmd` asserts the fitted mixture on every render,
in two layers:

1. **Against the published representation** — `identical(round(fit, 4), REF)`.
   Not a tolerance: the property that matters is whether the fit still rounds
   to the four-decimal matrix the manuscripts print, and two values can sit
   within any epsilon of each other and round to different fourth decimals.
   The reference is the prior-component table in `rerun/VERIFIED_NUMBERS.md`
   §5:

   | component | w | a | b |
   |---|---:|---:|---:|
   | informative | 0.5887 | 18.4026 | 53.2729 |
   | second | 0.2113 | 1.9564 | 4.7033 |
   | robust (flat) | 0.2000 | 1.0000 | 1.0000 |

   Mixture mean 0.3132.

2. **Against `simulation/map_prior_frozen.R`**, by explicit maximum absolute
   difference against a stated 1e-12 bound. **This one is a diagnostic, not a
   gate** — see below.

`map_prior_frozen.R` is not merely a reference — it **is** the prior the
simulations run on. The refit above is a validation calculation, so the
operating characteristics do not depend on a live `RBesT` call. The file is
required and never recreated automatically; regenerating on absence would let a
changed fit quietly install itself as the new reference, which is the failure
the whole mechanism exists to prevent. To create it deliberately:

```r
dput(prior_fitted_canon, "map_prior_frozen.R", control = c("all", "hexNumeric"))
```

`hexNumeric` writes binary fractions, which R documents as the exact
round-trip format. `digits17` is not sufficient — it was tried, and produced a
one-ulp discrepancy in two entries. With `hexNumeric` the frozen file and the
refit are bitwise equal, so making the file the simulation input provably moves
nothing.

Components are canonicalised by descending `a`, and dimnames dropped, before
comparison, so neither check depends on the order or the component names
`automixfit()` and `robustify()` happen to return.

The checks run in an **uncached preflight immediately after the fit**, before
any expensive chunk, so a failure costs seconds rather than a 30–60 minute
render. The assignment `prior_mix <- dget(...)` stays in the *cached* chunk: R
`autodep` covers cached chunks only, so setting it from an uncached chunk would
leave downstream cached results computed from the previous prior with nothing
to signal it. That cached chunk carries `cache.extra = tools::md5sum(...)` on
the frozen file, because `autodep` tracks objects and cannot see a file read.

Previously the only check was that the mixture weights summed to one, which is
true of every mixture and cannot fail.

## Reproduction and certification are separate

The two checks have different consequences, because they answer different
questions.

**Layer 1 is a hard stop, everywhere.** If the refit no longer rounds to the
published four-decimal table, the rendered document contradicts the prior table
printed in both manuscripts. That is a correctness failure wherever it happens.

**Layer 2 warns and records.** A deviation means this environment does not
reproduce the recorded fit. It does **not** mean the results are wrong: the
simulations run on `map_prior_frozen.R`, so a refit that differs cannot move a
single operating characteristic. Blocking on it would stop a replicator — a
different BLAS could shift the `gMAP` fit at 1e-11 — from reproducing results
that do not depend on the quantity that differed. So the render prints a
banner, raises an R warning that knitr renders into the HTML, and continues.

**Certification is where the strict requirement lives.** Every render writes
`simulation/map_prior_status.txt`, and the release checker gates on it:

```bash
python3 tools/release/check_release.py \
  --manifest tools/release/copies.example.toml --workspace . --only map_prior
```

That check requires `rounds_to_published_4dp`, `within_bound`, and — because
`copies.example.toml` sets `require_bitwise = true` — bitwise equality, which
holds on the producing machine thanks to `hexNumeric`. A release must not be
cut from a render whose status file fails it. The `[map_prior]` manifest table
is optional; an absent one skips the check with a note rather than failing, so
manifests written before this existed keep working.

So: **a replicator can reproduce the operating characteristics on any machine.
Only the author can certify a release, and only from the producing one.**

`simulation/SESSION_INFO.txt` is written by the render and records the actual
environment each time. It is committed, so the environment travels with the
results rather than living only in a gitignored HTML file.

## Reproducing

```r
install.packages(c("RBesT", "ggplot2", "dplyr", "tibble", "purrr",
                   "tidyr", "knitr", "patchwork", "scales"))
```

A LaTeX toolchain is also required — `simulation_study.qmd` declares both an
HTML and a PDF format, so a bare `quarto render` builds both and will fail at
the end of an hour-long render without it. Either install TinyTeX
(`quarto install tinytex`) or render HTML only:

```bash
cd simulation
quarto render simulation_study.qmd --to html
```

Exact cross-environment numerical identity is not claimed. Seeds are fixed and
per-cell, so a matching environment reproduces the published values; a
different one may not, and the assertions above are there to make that visible
rather than silent.

An `renv.lock` has not been generated. It is the right next step and would
replace this file.
