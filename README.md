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

The efficacy threshold is calibrated at a single assumed control rate. The study
asks whether that point calibration delivers Type I error control across the
composite null, and uses component ablations to see whether switching the
adaptive components off restores it.

### Key findings

- **Point calibration does not deliver control across the composite null.** With
  the threshold calibrated to α = 0.025 at the design anchor p₀ = 0.25, Type I
  error rises monotonically with the common baseline rate, reaching 0.2618 with
  all mechanisms active at p = 0.36 (and 0.1732 for the SSR/RAR-disabled
  ablation, which carries the same uncalibrated threshold).
- **Switching the adaptive components off does not restore control.** With SSR
  and RAR disabled but the full-design threshold retained, T1E is 0.1170 at
  p = 0.30. Note this ablation is **not separately calibrated** — it sits near
  0.05 at the anchor, twice nominal — so it is not an attributable share.
- **Composition modifies the excess nonlinearly, and its sign depends on where
  in the null the design is evaluated.** RAR has essentially no marginal effect
  without SSR (−0.0018) but adds +0.0314 when SSR is active (interaction
  +0.0332, 95% SI [+0.0144, +0.0520]). The net composition effect runs from
  −0.0212 at p = 0.20 to +0.0886 at p = 0.36.
- **Baseline-rate departure and time trends are super-additive** (interaction
  +0.0288, 95% SI [+0.0136, +0.0440]).

### Scope and limitations

- The grid **demonstrates** a control failure and establishes that the supremum
  is at least 0.2618. It does not locate the supremum.
- Scenarios are departures of the baseline rate from the **calibration anchor**
  p₀ = 0.25, not quantified prior-data conflict (which would be defined against
  the prior predictive distribution). Note the anchor is not the mean of any
  prior in play: the dominant component has mean 0.2568, the full robustified
  mixture 0.3132, the historical pooled rate 0.2533.
- Calibration is **in-sample**: grid-free binary search targets the empirical
  calibration sample, not the population Type I error.
- **Component ablations are not separately calibrated.** γ* is calibrated once,
  with all mechanisms active; every ablation retains it. With SSR and RAR
  disabled the ablation sits near 0.05 at the anchor. These rows answer "does
  switching this component off restore control?", not "how much of the excess
  did it cause?".
- The Version B comparison is an **SSR-timing sensitivity analysis**, not a
  clean negative control: moving SSR also changes the realised final sample-size
  distribution.
- The SSR rule is a pooled one-sample conditional-power test against p₀ = 0.25
  while the estimand is the two-arm comparison.

### Reproducibility notes

The SSR × RAR interaction is re-estimated on a fresh seed in the same R
implementation. This is an **executable chunk** in the simulation document
(`factorial-fresh-seed`, seed 73028, N = 3,000 per cell), not a reported
number — rendering the document reproduces it. Note that a repeat within the
same implementation guards against a seed artefact, not against a shared
modelling error.

An independent Python reimplementation gave a smaller estimate for this
interaction (+0.0098) with an interval containing zero, so its magnitude rests
on the R runs and should be read with that in mind.

Posterior probabilities are computed by deterministic Gauss–Legendre quadrature
rather than Monte Carlo, so monitoring decisions are not randomized.

## Repository structure

```
composed-adaptive-validation/
├── manuscript/
│   ├── JSM_2026_Manuscript.tex    # LaTeX manuscript source
│   ├── references.bib             # BibTeX bibliography
│   └── figures/                   # All manuscript figures
│       ├── Figure1_Composed_Design.png
│       ├── composite-null-plot-1.png
│       ├── results-plot-1.png
│       ├── factorial-1.png
│       ├── mechanism-isolation-1.png
│       ├── sens-panel-1.png
│       ├── map-prior-validation-1.png
│       └── calibration-1.png
├── simulation/
│   ├── simulation_study.qmd       # Quarto simulation (R)
│   ├── custom.scss                # HTML theme overrides
│   └── references.bib             # Simulation bibliography
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

This produces a self-contained HTML report with all figures, tables, and diagnostic output. Full runtime is approximately 15-30 minutes depending on hardware (10,000 trial replications per scenario, multiple sensitivity sweeps).

### Seeds

All random seeds are fixed for exact reproducibility. See the Seeds table at the end of the simulation document for the complete list.

## Compiling the manuscript

```bash
cd manuscript
pdflatex JSM_2026_Manuscript.tex
bibtex JSM_2026_Manuscript
pdflatex JSM_2026_Manuscript.tex
pdflatex JSM_2026_Manuscript.tex
```

## Presentations

This work is presented at:

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
