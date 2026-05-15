# Composed Adaptive Trial Validation

**Type I Error Inflation in Composed Adaptive Bayesian Clinical Trial Designs**

Lu Qian  
Zetyra / Evidence in the Wild, LLC  
[maggie@zetyra.com](mailto:maggie@zetyra.com)

---

## Overview

This repository contains the manuscript and simulation code for a study demonstrating that component-level validation is insufficient for composed adaptive clinical trial designs. When Bayesian monitoring, sample size re-estimation (SSR), and response-adaptive randomization (RAR) share overlapping information sets at interim analyses, two failure mechanisms — prior-data conflict and time trends — inflate Type I error at the pipeline level even when every component individually passes its validation check.

### Key findings

- Under a mild prior-data conflict (2 pp above the prior mean), pipeline-level Type I error reaches 0.077 (+208% above nominal alpha = 0.025).
- A negative control moving SSR to an earlier interim shows negligible attenuation, identifying prior-data conflict as the dominant driver.
- The two mechanisms are super-additive (interaction = +0.028, 95% simulation interval excluding zero).
- Component-level calibration guarantees are not invariant under composition.

## Repository structure

```
composed-adaptive-validation/
├── manuscript/
│   ├── JSM_2026_Manuscript.tex    # LaTeX manuscript source
│   ├── references.bib             # BibTeX bibliography
│   └── figures/                   # All manuscript figures
│       ├── Figure1_Composed_Design.png
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

This work will be presented at:

- **JSM 2026** — Session: AI, Machine Learning & Digital Tools in Clinical Development (August 3, 2026)
- **RISW 2026** — Panel: Regulatory Innovation in Adaptive & Bayesian Trial Design (August 2026)

## Citation

```bibtex
@inproceedings{qian_composed_2026,
  author    = {Qian, Lu},
  title     = {Zetyra: A Validated, Regulatory-Aligned Calculator Suite
               for Adaptive and Bayesian Clinical Trial Design},
  booktitle = {Proceedings of the Joint Statistical Meetings},
  year      = {2026},
  address   = {Boston, MA},
  url       = {https://github.com/evidenceinthewild/Composed-Adaptive-Trial-Validation}
}
```

## Related resources

- [Zetyra whitepaper (v2.0)](https://zetyra.com/whitepaper) — Full validation framework and calculator documentation
- [Zenodo archive](https://doi.org/10.5281/zenodo.18879839) — Citable versioned snapshot

## License

This work is licensed under the MIT License. See [LICENSE](LICENSE) for details.
