#!/usr/bin/env Rscript
# ═══════════════════════════════════════════════════════════════════════════
# Paired diagnostic for the quadrature approximation in map_posterior_prob()
#
# WHY THIS EXISTS
# The simulation computes P(p_e > p_c | data) by 400-node Gauss-Legendre
# quadrature rather than Monte Carlo, because the monitoring rule takes a
# maximum over interim looks and Monte Carlo noise inflates that maximum.
# The supplement previously called that computation "exact". It is
# DETERMINISTIC, not exact: the integrand is smooth over most of the parameter
# space, but extreme all-success states concentrate posterior mass near the
# boundary, where 400 nodes leave visible error.
#
# This script makes that statement reproducible rather than asserted. It
# reports the deviation between quadrature and a high-draw Monte Carlo
# reference across a grid of states that deliberately includes the boundary.
#
# NOTE ON WHAT A MONTE CARLO REFERENCE CAN ESTABLISH
# A reference with M draws carries its own standard error of order 1/sqrt(M):
# about 1.6e-3 at M = 4e5. Agreement can therefore only be demonstrated to
# that scale. An earlier version of the supplement claimed agreement "to
# ~1e-16", which is not attainable by this comparison.
#
# Usage:  Rscript composed-adaptive-validation/simulation/quadrature_diagnostic.R
# Needs:  RBesT (for the same prior the study uses)
# Runtime: about a minute
# ═══════════════════════════════════════════════════════════════════════════

suppressPackageStartupMessages(library(RBesT))

SEED    <- 20260727L   # fixed: this diagnostic must be reproducible
M_DRAWS <- 4e5L        # Monte Carlo reference draws per state
N_NODES <- 400L        # quadrature nodes, matching the simulation

set.seed(SEED)

# ── the study's prior, refitted here so the script stands alone ──────────────
hist_dat <- data.frame(study = paste0("H", 1:3),
                       n = c(50, 40, 60), r = c(13, 10, 15))
map_mc   <- gMAP(cbind(r, n - r) ~ 1 | study, data = hist_dat,
                 family = binomial, tau.dist = "HalfNormal",
                 tau.prior = 0.5, beta.prior = 2)
rob_mix  <- robustify(automixfit(map_mc, Nc = 2), weight = 0.2, mean = 0.5)
mix      <- rbind(w = rob_mix[1, ], a = rob_mix[2, ], b = rob_mix[3, ])

mixture_posterior <- function(mix, x, n) {
  a <- mix["a", ] + x; b <- mix["b", ] + (n - x)
  lw <- log(mix["w", ]) + lbeta(a, b) - lbeta(mix["a", ], mix["b", ])
  rbind(w = exp(lw - matrixStats::logSumExp(lw)), a = a, b = b)
}

# ── Golub-Welsch Gauss-Legendre nodes on (0, 1), as in the simulation ────────
gl <- local({
  i <- 1:(N_NODES - 1); b <- i / sqrt(4 * i^2 - 1)
  e <- eigen(diag(0, N_NODES) + diag(b, N_NODES, N_NODES)[, , drop = FALSE] +
               t(diag(b, N_NODES, N_NODES)), symmetric = TRUE)
  x <- rev(e$values); w <- 2 * rev(e$vectors[1, ])^2
  list(x = (x + 1) / 2, w = w / 2)
})

p_quad <- function(x_e, n_e, x_c, n_c) {
  post <- mixture_posterior(mix, x_c, n_c)
  f_e  <- dbeta(gl$x, 0.5 + x_e, 0.5 + (n_e - x_e))
  F_c  <- rowSums(vapply(seq_len(ncol(post)),
                         function(j) post["w", j] *
                           pbeta(gl$x, post["a", j], post["b", j]),
                         numeric(length(gl$x))))
  sum(gl$w * f_e * F_c)
}

p_mc <- function(x_e, n_e, x_c, n_c, M = M_DRAWS) {
  post <- mixture_posterior(mix, x_c, n_c)
  k    <- sample.int(ncol(post), M, replace = TRUE, prob = post["w", ])
  pc   <- rbeta(M, post["a", ][k], post["b", ][k])
  pe   <- rbeta(M, 0.5 + x_e, 0.5 + (n_e - x_e))
  mean(pe > pc)
}

# ── state grid: interim looks the design actually visits, PLUS the boundary ──
states <- expand.grid(n = c(30L, 45L, 60L, 90L), frac_e = c(0, .25, .5, .75, 1),
                      frac_c = c(0, .25, .5, .75, 1))
states$n_e <- states$n %/% 2L; states$n_c <- states$n - states$n_e
states$x_e <- round(states$frac_e * states$n_e)
states$x_c <- round(states$frac_c * states$n_c)

res <- do.call(rbind, lapply(seq_len(nrow(states)), function(i) {
  s <- states[i, ]
  q <- p_quad(s$x_e, s$n_e, s$x_c, s$n_c)
  m <- p_mc(s$x_e, s$n_e, s$x_c, s$n_c)
  data.frame(n = s$n, x_e = s$x_e, n_e = s$n_e, x_c = s$x_c, n_c = s$n_c,
             quad = q, mc = m, dev = abs(q - m),
             boundary = (s$x_e == s$n_e) || (s$x_c == s$n_c) ||
                        (s$x_e == 0) || (s$x_c == 0))
}))

mc_se <- 0.5 / sqrt(M_DRAWS)   # worst-case SE of the reference itself
cat(sprintf("\nseed %d | %d nodes | %.0e reference draws\n", SEED, N_NODES, M_DRAWS))
cat(sprintf("reference Monte Carlo SE (worst case) : %.2e\n", mc_se))
cat(sprintf("max |quad - mc|, interior states      : %.2e\n",
            max(res$dev[!res$boundary])))
cat(sprintf("max |quad - mc|, boundary states      : %.2e\n",
            max(res$dev[res$boundary])))
cat(sprintf("states exceeding 3x the reference SE  : %d of %d\n",
            sum(res$dev > 3 * mc_se), nrow(res)))
cat("\nWorst ten states:\n")
print(head(res[order(-res$dev), ], 10), row.names = FALSE, digits = 4)

cat("\n---\nInterpretation: deviations at or below the reference SE are not\n",
    "evidence of quadrature error -- they are the reference's own noise.\n",
    "Deviations concentrated on boundary states are the approximation error\n",
    "the supplement now acknowledges.\n\n",
    "The companion claim -- that gamma* and the reported T1E cells are\n",
    "unchanged -- is a separate, more expensive check: re-run the calibration\n",
    "and factorial chunks with N_NODES set to 400 and to 2000 and compare.\n",
    "That comparison is not performed here because it requires the full\n",
    "simulation, not a single-integral diagnostic.\n", sep = "")
