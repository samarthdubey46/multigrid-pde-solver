# AGENTS.md

## Project overview

This repository contains small Python experiments for multigrid-preconditioned
Poisson solvers:

- `main.py` compares plain CG, digital multigrid-preconditioned CG, and a
  noisy/photonic hybrid variant on a 2D Poisson problem.
- `smoother.py` explores a 1D multigrid V-cycle and PCG workflow, including a
  residual-history plot.

## Environment and execution

- Use the existing `venv` virtual environment when available.
- Required libraries are NumPy, SciPy, PyAMG, and Matplotlib (for
  `smoother.py`).
- Run an experiment with `python main.py` or `python smoother.py`.
- There is no test suite or packaging configuration yet. For behavioral
  changes, run the affected script and check that it completes and reports a
  finite relative residual.

## Numerical implementation guidance

- Preserve sparse matrices and sparse operations; avoid converting to dense
  matrices except for the deliberately tiny coarsest-grid solve in
  `smoother.py`.
- Keep vector dimensions compatible with the operator/grid shape and preserve
  homogeneous Dirichlet boundary assumptions unless the task explicitly
  changes the model.
- Treat random behavior as deliberate: `main.py` uses a seeded NumPy generator
  for reproducible analog-noise experiments.
- Maintain the matrix-vector-product counters in `main.py` when changing solver
  paths; they are part of the reported comparison.
- Use relative residuals to assess solver convergence. Do not silently loosen
  tolerances or iteration limits.

## Code style

- Follow the existing straightforward Python style and keep experimental
  parameters near the top of each script.
- Prefer small, named functions for numerical steps (smoothing, V-cycles,
  preconditioning, and solve loops).
- Add concise comments or docstrings for algorithmic choices that are not
  apparent from the linear algebra.
