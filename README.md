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

- **Point calibration does not deliver control across the composite null.** With
  the threshold calibrated to α = 0.025 at the design anchor p₀ = 0.25, the
  design performs as intended at the anchor itself (Type I error 0.0236 against
  a nominal 0.025) but not away from it. Holding the rate constant over calendar
  time — so that every rejection is a Type I error in the conventional sense —
  changing only the common baseline rate gives 0.0810 at p = 0.30, 0.1854 at
  p = 0.36 and 0.2786 at p = 0.45, with the curve still climbing at the grid
  boundary. **No calendar trend and no misspecified analysis are needed.**
- **A separate trend-active grid is reported as a stress analysis.** Both arms
  drift together under a time-constant analysis, so there is still no
  contemporaneous treatment effect, but rejections there are *not* Type I errors
  and are reported as rejection probabilities. That grid reaches 0.2874.
- **Switching the adaptive components off does not restore control.** With SSR
  and RAR disabled but the full-design threshold retained, the constant-rate
  Type I error is still 0.0936 at p = 0.30 and 0.2020 at p = 0.45. This ablation
  is **not separately calibrated**, so its difference from the full design is
  not an attributable share — and the SSR-enabled cells additionally accrue a
  fifth interim look whenever SSR extends enrollment.
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

- The grid **demonstrates** a control failure and establishes that the supremum
  of the Type I error is at least 0.2786. It does not locate the supremum, and
  the curve has not flattened at the grid boundary. The two largest rates
  (0.40, 0.45) characterise the shape of the curve rather than representing
  plausible control rates: the mixture prior has mean 0.3132, and p = 0.45
  is numerically equal to the experimental-arm rate assumed under the planning
  alternative (against a 0.25 control). That row is still a **null**: both arms
  sit at 0.45, so there is no treatment effect, and the coincidence is
  arithmetic only. Over the clinically motivated
  range — departures of two to eleven percentage points from the anchor —
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
implementation (`factorial-fresh-seed`, seed 73028, N = 3,000 per cell).
Both the primary and fresh-seed simulation intervals include zero.
A repeat within the same implementation guards against a seed artefact, not
against a shared modelling error.

Posterior probabilities are computed by deterministic Gauss–Legendre quadrature
rather than Monte Carlo, so monitoring decisions are not randomized.

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
│   ├── custom.scss                # HTML theme overrides
│   └── references.bib             # Simulation bibliography
├── tools/release/                 # Read-only public-release checks
├── README.md
├── LICENSE
└── .gitignore
```

## Reproducing the simulation

### Prerequisites

- **R** (>= 4.2)
- **Quarto** (>= 1.3)
- R packages: `RBesT`, `ggplot2`, `dplyr`, `tibble`, `purrr`, `tidyr`, `knitr`, `patchwork`, `scales`

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
diagnostic output. To build only the HTML report, add `--to html`. Full
runtime is approximately 15–30 minutes depending on hardware (10,000 trial
replications per scenario, multiple sensitivity sweeps).

### Seeds

All random seeds are fixed for exact reproducibility. See the Seeds table at the end of the simulation document for the complete list.

## Compiling the manuscript

```bash
cd manuscript
xelatex JSM_2026_Manuscript.tex
bibtex JSM_2026_Manuscript
xelatex JSM_2026_Manuscript.tex
xelatex JSM_2026_Manuscript.tex
```

## Release checks

Run these commands from the repository root after rendering the simulation:

    python3 tools/release/test_release_tools.py
    python3 tools/release/check_release.py \
      --manifest tools/release/copies.example.toml \
      --workspace .

## Scheduled presentations

This work is scheduled for:

- **JSM 2026** — Session: AI, Machine Learning & Digital Tools in Clinical Development (August 3, 2026)
- **RISW 2026** — Panel: Regulatory Innovation in Adaptive & Bayesian Trial Design (September 2026)

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
