#!/usr/bin/env Rscript
# ═══════════════════════════════════════════════════════════════════════════
# Node-count sensitivity of the quadrature in map_posterior_prob()
#
# WHY THIS EXISTS
# The simulation computes P(p_e > p_c | data) by Gauss-Legendre quadrature
# rather than Monte Carlo, because the monitoring rule takes a maximum over
# interim looks and Monte Carlo noise inflates that maximum. Quadrature is
# DETERMINISTIC, not exact. This script measures where the approximation error
# lives and how it responds to the node count.
#
# HISTORY (read this before trusting any diagnostic)
# The first version of this script REIMPLEMENTED the Gauss-Legendre node
# construction instead of reusing the simulation's, and got it wrong: it built
# the Jacobi matrix with `diag(b, n, n)`, putting the off-diagonal terms on the
# MAIN diagonal. The resulting rule still integrated the constant 1 to exactly
# 1.0 and still produced nodes inside (0, 1), so its output looked plausible.
# It integrated x to 0.7887 instead of 0.5.
#
# Two consequences are built into this rewrite:
#   1. The node construction below is COPIED VERBATIM from the simulation's
#      gauss_legendre_01(). A diagnostic that reimplements what it is checking
#      is not a check.
#   2. Every claim this script makes is guarded by a self-test that HALTS.
#      A wrong rule now fails at the first moment test rather than reporting
#      confident nonsense.
#
# Exit status: 0 if all tolerances hold, 1 otherwise.
#
# Usage:   Rscript composed-adaptive-validation/simulation/quadrature_diagnostic.R
# Needs:   base R only
# Runtime: a few seconds
# ═══════════════════════════════════════════════════════════════════════════

N_SIM  <- 400L    # node count the simulation uses
N_REF  <- 2000L   # reference node count for the paired comparison
fail   <- 0L

report <- function(ok, msg, detail = "") {
  if (!ok) fail <<- fail + 1L
  cat(sprintf("  %-6s %s%s\n", if (ok) "ok" else "FAIL", msg,
              if (nzchar(detail)) paste0("  [", detail, "]") else ""))
}

# ── node construction: VERBATIM from simulation_study.qmd ────────────────────
gauss_legendre_01 <- function(n) {
  k <- 1:(n - 1)
  b <- k / sqrt(4 * k^2 - 1)
  J <- diag(0, n)
  J[cbind(k, k + 1)] <- b
  J[cbind(k + 1, k)] <- b
  e <- eigen(J, symmetric = TRUE)
  ord <- order(e$values)
  x <- e$values[ord]
  w <- 2 * (e$vectors[1, ord])^2
  list(x = (x + 1) / 2, w = w / 2)          # map [-1,1] -> [0,1]
}

cat("\n== 1. self-tests on the quadrature rule ==\n")
cat("   (the earlier broken version passed the first of these and failed the rest)\n")
for (n in c(8L, N_SIM)) {
  g <- gauss_legendre_01(n)
  report(abs(sum(g$w) - 1) < 1e-12,
         sprintf("n=%-4d integral of 1   = 1", n),
         sprintf("err %.2e", abs(sum(g$w) - 1)))
  report(abs(sum(g$w * g$x) - 0.5) < 1e-12,
         sprintf("n=%-4d integral of x   = 1/2", n),
         sprintf("err %.2e", abs(sum(g$w * g$x) - 0.5)))
  report(abs(sum(g$w * g$x^2) - 1/3) < 1e-12,
         sprintf("n=%-4d integral of x^2 = 1/3", n),
         sprintf("err %.2e", abs(sum(g$w * g$x^2) - 1/3)))
  report(all(g$x > 0 & g$x < 1) && all(g$w > 0),
         sprintf("n=%-4d nodes in (0,1), weights positive", n))
}
# exactness to degree 2n-1 is the property that distinguishes a real
# Gauss-Legendre rule from an arbitrary set of positive weights
g8 <- gauss_legendre_01(8L); d <- 2 * 8 - 1
report(abs(sum(g8$w * g8$x^d) - 1 / (d + 1)) < 1e-10,
       sprintf("n=8    exact to degree 2n-1 = %d", d),
       sprintf("err %.2e", abs(sum(g8$w * g8$x^d) - 1 / (d + 1))))

if (fail > 0L) {
  cat("\n! the quadrature rule itself is wrong; nothing below would be meaningful\n")
  quit(status = 1L)
}

# ── 2. where the error lives: Beta normalisation across the state space ──────
# The integrand is a Beta density. If the rule cannot integrate that density to
# 1, it cannot be trusted on this state. Extreme all-success / all-failure
# states put nearly all mass at a boundary, which is where a fixed-node rule
# struggles.
cat("\n== 2. Beta normalisation by state (n =", N_SIM, "vs", N_REF, ") ==\n")
gs <- gauss_legendre_01(N_SIM)
gr <- gauss_legendre_01(N_REF)

states <- rbind(
  data.frame(lab = "interior      (x=23, n=45)",       a = 0.5 + 23, b = 0.5 + 22),
  data.frame(lab = "all successes (x=45, n=45)",       a = 0.5 + 45, b = 0.5 +  0),
  data.frame(lab = "all failures  (x= 0, n=45)",       a = 0.5 +  0, b = 0.5 + 45),
  data.frame(lab = "all successes (x=90, n=90)",       a = 0.5 + 90, b = 0.5 +  0),
  data.frame(lab = "near boundary (x=44, n=45)",       a = 0.5 + 44, b = 0.5 +  1))

worst_interior <- 0
for (i in seq_len(nrow(states))) {
  s  <- states[i, ]
  ns <- sum(gs$w * dbeta(gs$x, s$a, s$b))
  nr <- sum(gr$w * dbeta(gr$x, s$a, s$b))
  boundary <- grepl("all |near", s$lab)
  cat(sprintf("  %-28s n=%d: %.10f   n=%d: %.10f   |diff| %.2e%s\n",
              s$lab, N_SIM, ns, N_REF, nr, abs(ns - nr),
              if (boundary) "   <- boundary" else ""))
  if (!boundary) worst_interior <- max(worst_interior, abs(ns - 1))
}
report(worst_interior < 1e-8,
       "interior states normalise to 1 at the simulation's node count",
       sprintf("worst %.2e", worst_interior))

# ── 3. what this does and does not establish ─────────────────────────────────
cat("\n== 3. scope ==\n")
cat("  Established: the rule is a valid Gauss-Legendre rule; interior states\n")
cat("  integrate to machine precision; boundary states do not, and the\n")
cat(sprintf("  disagreement between %d and %d nodes there is the size of the\n",
            N_SIM, N_REF))
cat("  approximation error, not of Monte Carlo noise.\n\n")
cat("  NOT established: that gamma* or any reported T1E cell is unchanged by\n")
cat("  the node count. That requires re-running the calibration and factorial\n")
cat(sprintf("  chunks end to end with N_NODES set to %d and to %d and comparing.\n",
            N_SIM, N_REF))
cat("  This script deliberately does not claim it.\n")

cat(sprintf("\n%s (%d failed check%s)\n",
            if (fail == 0L) "PASS" else "FAIL", fail, if (fail == 1L) "" else "s"))
quit(status = if (fail == 0L) 0L else 1L)
