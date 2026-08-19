# Composed Adaptive Trial Validation

**Point Calibration Does Not Control Type I Error Across the Composite Null
in a Composed Adaptive Bayesian Design**

Lu Qian  
Zetyra | Evidence in the Wild  
[maggie@zetyra.com](mailto:maggie@zetyra.com)

---

## Overview

This repository contains the manuscript and simulation code for a study of Type I
error control in a two-arm Phase II oncology design with historical borrowing on
the control arm, Bayesian posterior monitoring, blinded sample size re-estimation
(SSR), and response-adaptive randomization (RAR).

The primary SSR implementation is **Rule B**: the pooled interim response rate
is used only as a blinded nuisance-parameter estimate, the planned treatment
effect remains fixed at 0.20, and sample size is recomputed under a prespecified
working 1:1 allocation. This follows the binary internal-pilot principle of
Friede and Kieser (2004). It is a conventional-style working rule, not an exact
power calculation for the downstream RAR/Bayesian design.

The efficacy threshold is calibrated at a single assumed control rate. The study
asks whether that point calibration delivers Type I error control across the
composite null, and uses component ablations to see whether switching the
adaptive components off restores it.

### Key findings

- **Point calibration does not deliver control across the composite null.** The
  simulations evaluate the constant-rate equality boundary of the superiority
  null, $H_0:p_e\le p_c$. With
  the threshold calibrated to α = 0.025 at the design anchor p₀ = 0.25, the
  design performs as intended at the anchor itself (Type I error 0.0236 against
  a nominal 0.025) but not away from it. Holding the rate constant over calendar
  time — so that every rejection is a Type I error in the conventional sense —
  changing only the common baseline rate gives 0.0810 at p = 0.30, 0.1854 at
  p = 0.36 and 0.2786 at p = 0.45, with the curve still climbing at the grid
  boundary. **No calendar trend or time-model misspecification is needed.**
- **A separate trend-active grid is reported as a stress analysis.** Both arms
  drift together under a time-constant analysis, so there is still no
  contemporaneous treatment effect. Those rejections are kept outside the
  paper's constant-rate Type I error estimand and are reported as rejection
  probabilities. That grid reaches 0.2874.
- **Switching the adaptive components off does not restore control.** With SSR
  and RAR disabled but the full-design threshold retained, the constant-rate
  Type I error is still 0.0936 at p = 0.30 and 0.2020 at p = 0.45. This ablation
  is **not separately calibrated**, so its difference from the full design is
  not an attributable share — and the SSR-enabled cells additionally receive a
  fifth efficacy analysis whenever SSR extends enrollment.
- **The sign of the composition contrast depends on where in the null the
  design is evaluated.** The full-minus-ablation contrast runs from −0.0250 at
  p = 0.20 to +0.0904 at p = 0.45 on the trend-active grid.
- **The interaction estimates do not support a claim in either direction.** The
  SSR × RAR interaction was estimated twice: −0.0240 (95% SI [−0.0419, −0.0061],
  N = 5,000/cell) and −0.0037 ([−0.0126, +0.0052], N = 20,000/cell). The
  inverse-variance pooled estimate is **−0.0077 ([−0.0157, +0.0002])**, which
  includes zero; we report the pooled value and draw no directional conclusion.
  The departure × trend interaction is −0.0006 ([−0.0145, +0.0133]).

### Scope and limitations

- The constant-rate grid covers only $p_e=p_c=p$, a one-dimensional boundary
  slice of the superiority null. A violation anywhere on that boundary is enough
  to refute uniform control, but the study does not establish the least-favorable
  configuration or characterize the interior $p_e<p_c$.
- The grid **demonstrates** a control failure. The largest *estimated* Type I
  error is 0.2786 (MCSE 0.0063) — a point estimate, not a bound. But since the
  supremum is at least the value at any evaluated point, the one-sided 95%
  simulation limit at p = 0.45 gives a probabilistic **lower** bound: the
  supremum is at or above **0.2682**. That 95% is *conditional on the selected*
  γ\* — it covers Monte Carlo error at that rate and does not propagate the
  calibration-sample uncertainty in the threshold (bootstrap SD 0.00106), so it
  is not an unconditional statement. It does not
  locate the supremum or provide an upper bound, and the curve has not flattened
  at the grid boundary. The two largest rates (0.40, 0.45) characterise the
  shape of the curve; the study does not assert that they are plausible control
  rates for this indication. The value p = 0.45 is numerically equal to the
  experimental-arm rate assumed under the planning
  alternative (against a 0.25 control). That row is still a **null**: both arms
  sit at 0.45, so there is no treatment effect, and the coincidence is
  arithmetic only. Over the lower evaluated range — departures of two to
  eleven percentage points from the anchor —
  Type I error runs from 0.0380 to 0.1854.
- Scenarios are departures of the baseline rate from the **calibration anchor**
  p₀ = 0.25, not quantified prior-data conflict (which would be defined against
  the prior predictive distribution). Note the anchor is not the mean of any
  prior in play: the dominant component has mean 0.2568, the full robustified
  mixture 0.3132, the historical pooled rate 0.2533.
- Grid-free calibration gives γ* = 0.96566 and in-sample T1E = 0.0248. A
  fresh-seed validation gives 0.0224 (95% SI [0.0183, 0.0265]), compatible with
  nominal; neither finite simulation establishes the population rate exactly.
- **Component ablations are not separately calibrated.** γ* is calibrated once,
  with all mechanisms active; every ablation retains it. These rows answer "does
  switching this component off restore control?", not "how much of the excess
  did it cause?".
- Moving Rule B from n = 45 to n = 30 is an **SSR-timing sensitivity analysis**, not a
  clean negative control: moving SSR also changes the realised final sample-size
  distribution.
- Rule B uses a 1:1 Wald working model and preserves the reference power implied
  by N = 90 (0.5296). Its actual n = 45 mapping is narrow (N = 90–100), despite
  the protocol cap of 150. It is blinded and nuisance-based, but it is not an
  exact power calculation for RAR or the Bayesian final rule. With trend
  anchored to the planned N = 90 horizon, the largest possible terminal drift
  under this primary mapping is approximately 0.0556.
- The original, more aggressive Rule A pooled conditional-power results are
  retained only in the manuscript appendix as a labeled stress test and
  method-development record. They are not the primary analysis.

### Reproducibility notes

The SSR × RAR interaction is re-estimated by an executable chunk in the same R
implementation (`factorial-fresh-seed`, per-cell seeds 800000 + 1000·k,
N = 20,000 per cell). The primary interval **excludes** zero; the
higher-precision replicate and the inverse-variance pooled estimate both
include it, and the pooled value is what we report.
A repeat within the same implementation guards against a seed artefact, not
against a shared modelling error.

Posterior probabilities are computed by deterministic Gauss–Legendre quadrature
rather than Monte Carlo, so monitoring decisions are not randomized. The
reported operating characteristics are conditional on the specified 400-node
rule; the targeted 12-state comparison is not an exhaustive audit of every
reachable state or every integration rule.

## Repository structure

```
composed-adaptive-validation/
├── manuscript/
│   ├── JSM_2026_Manuscript.tex    # LaTeX manuscript source
│   ├── JSM_2026_Manuscript.pdf    # Rendered manuscript
│   ├── references.bib             # BibTeX bibliography
│   └── figures/                   # Manuscript and supporting simulation figures
│       ├── Figure1_Composed_Design.png
│       ├── composite-null-plot-1.png
│       ├── results-plot-1.png
│       ├── factorial-1.png
│       ├── departure-trend-crossing-1.png
│       ├── sens-panel-1.png
│       ├── map-prior-validation-1.png
│       └── calibration-1.png
├── simulation/
│   ├── simulation_study.qmd       # Quarto simulation (R)
│   ├── map_prior_frozen.R         # The MAP mixture the simulations run on
│   ├── map_prior_status.txt       # Written each render; the release gate reads it
│   ├── SESSION_INFO.txt           # Written each render; producing environment
│   ├── custom.scss                # HTML theme overrides
│   └── references.bib             # Simulation bibliography
├── tools/release/                 # Read-only public-release checks
├── SOFTWARE_ENVIRONMENT.md        # Producing versions and the prior invariant
├── README.md
├── LICENSE
└── .gitignore
```

### The frozen prior

`simulation/map_prior_frozen.R` is not a reference copy — it **is** the prior
the simulations run on, committed in `hexNumeric` form so it round-trips
bit for bit. The MAP refit that `RBesT` performs on every render is a
*validation calculation* checked against it, which is why an upgrade to RBesT
or Stan cannot silently move every number in the paper.

Each render checks two things and writes `map_prior_status.txt`:

- **the refit still rounds to the published four-decimal prior table** — a hard
  stop, because a change there would contradict the table the manuscript
  prints;
- **the refit reproduces the frozen mixture to 1e-12** — a diagnostic, not a
  gate. Results come from the frozen file, so a refit difference cannot change
  them, and a replicator on different hardware should not be blocked by a
  quantity that has no influence on the answer.

The strict version of the second check belongs to release certification, not to
reproduction:

    python3 tools/release/check_release.py \
      --manifest tools/release/copies.example.toml --workspace . --only map_prior

See [SOFTWARE_ENVIRONMENT.md](SOFTWARE_ENVIRONMENT.md).

## Reproducing the simulation

### Prerequisites

- **R** 4.6.1 — the version that produced the released results. Earlier
  versions are untested, and this matters more than it usually would:
  `robustify()` has returned `Beta(1,1)` or `Beta(0.5,0.5)` depending on `n`
  and the RBesT version, which would change the fitted mixture and every
  operating characteristic computed against it. See
  [SOFTWARE_ENVIRONMENT.md](SOFTWARE_ENVIRONMENT.md).
- **Quarto** (>= 1.3)
- **A LaTeX toolchain** — `simulation_study.qmd` declares both an HTML and a
  PDF format, so a bare `quarto render` builds both. Without TeX it fails at
  the end of a 30–60 minute run. Either `quarto install tinytex` or render HTML
  only (below).
- R packages: `RBesT` 1.10-0, `ggplot2`, `dplyr`, `tibble`, `purrr`, `tidyr`, `knitr`, `patchwork`, `scales`

### Installation

```r
install.packages(c("RBesT", "ggplot2", "dplyr", "tibble", "purrr",
                    "tidyr", "knitr", "patchwork", "scales"))
```

### Running

```bash
cd simulation
quarto render simulation_study.qmd
```

This produces self-contained HTML and PDF reports with all figures, tables, and
diagnostic output. To build only the HTML report, add `--to html`. Simulation
budgets vary by experiment: the main grid uses 5,000 replicates per cell, the
calibration uses 20,000, and the higher-precision factorial replicate uses
20,000 per cell.

### Seeds

All random seeds are fixed. They support reproduction in a matching software
environment, but exact numerical identity across platforms or package versions
is not claimed. See the Seeds table at the end of the simulation document for
the complete list.

## Compiling the manuscript

```bash
cd manuscript
pdflatex JSM_2026_Manuscript.tex
bibtex JSM_2026_Manuscript
pdflatex JSM_2026_Manuscript.tex
pdflatex JSM_2026_Manuscript.tex
```

This copy uses the repository's house format — 11 pt, 1 in margins, Computer
Modern — and its preamble contains no `fontspec` or engine branch, so pdfLaTeX
is the engine it is written for. The JSM Proceedings copy is a different
document with a different job: it is set to the ASA specification (10 pt Times
New Roman, 1 in top and bottom, 1.5 in left and right) and carries an `iftex`
branch so that XeLaTeX embeds Times New Roman itself. Do not build this one
with XeLaTeX expecting Times; it has nothing to switch to.

## Release checks

Run these commands from the repository root after rendering the simulation:

    python3 tools/release/test_release_tools.py
    python3 tools/release/check_release.py \
      --manifest tools/release/copies.example.toml \
      --workspace .

## Scheduled presentations

This work is scheduled for:

- **JSM 2026** — Session: AI, Machine Learning & Digital Tools in Clinical Development (August 3, 2026)
- **RISW 2026** — Session PS13, *Bayesian Methods Driving Transdisciplinary Decision-Making in Confirmatory Clinical Trials* (Thu 17 Sep 2026, Bethesda North Marriott)

## Citation

```bibtex
@inproceedings{qian_composed_2026,
  author    = {Qian, Lu},
  title     = {Point Calibration Does Not Control Type~{I} Error Across the
               Composite Null in a Composed Adaptive {B}ayesian Design},
  booktitle = {Proceedings of the Joint Statistical Meetings},
  year      = {2026},
  address   = {Boston, MA},
  url       = {https://github.com/evidenceinthewild/Composed-Adaptive-Trial-Validation}
}
```

## Related resources

- [Zetyra white paper, v2.3](https://doi.org/10.5281/zenodo.20218751) —
  benchmark framework and calculator documentation
  (DOI [10.5281/zenodo.20218751](https://doi.org/10.5281/zenodo.20218751);
  also at [zetyra.com/whitepaper](https://zetyra.com/whitepaper))

Note: that DOI identifies the **white paper**, not a versioned archive of this
study. A separate DOI should be minted for this repository before citing it as
an archived artifact.

## License

This work is licensed under the MIT License. See [LICENSE](LICENSE) for details.
