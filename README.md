# Photonic multigrid PDE solver

Interactive hardware mapping and numerical experiments for multigrid-preconditioned iterative Poisson solvers, inspired by Lee et al., *Integrated photonic multigrid solver for partial differential equations*.

Live website: [Detailed lab](https://samarthdubey46.github.io/multigrid-pde-solver/web/index.html) · [Continuous flowchart](https://samarthdubey46.github.io/multigrid-pde-solver/web/loop.html)

## Interactive pages

- [Detailed laboratory](web/index.html): guided hardware architecture, solver operations, vectors, matrices and diagnostics.
- [Continuous flowchart](web/loop.html): complete outer correction, PCG, recursive multigrid and optical feedback loop on one connected map.

Open either HTML file locally. Both are self-contained and work offline, with reciprocal navigation links. The browser demonstration solves a 64-unknown 1D problem with boundary values 100 and 0. It models ideal optical smoothing MVMs; CPU operations remain digital. It does not model physical device timing or claim measured hardware speedups.

## Presentation

[Download editable PowerPoint](presentation/output/photonic-pde-architecture.pptx): 19 main slides plus 16 technical appendix slides, with speaker notes, equations, matrices, measured graphs and sources. Research and generation files are in `presentation/`.

## Python experiments

Use a virtual environment with NumPy, SciPy, PyAMG and Matplotlib. Run `python main.py` for the 4096-unknown 2D comparison of CG, digital multigrid and noisy photonic hybrid solvers. `smoother.py` contains the earlier 1D prototype; its final diagnostic currently needs correction (`A` is a hierarchy list).

The Python configurations differ from the ideal browser demonstration. Counts measure algorithmic MVM calls, not hardware latency.

## Verification

`node web/verify.cjs --core-only` checks numerical baselines. Browser checks require Playwright and Chrome: `CHROME_PATH=/opt/google/chrome/chrome node web/verify.cjs` and `node web/verify-loop.cjs`. See [web documentation](web/README.md) for controls, scope and validation details.
