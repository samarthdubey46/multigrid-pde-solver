# Presentation brief

Audience: A professor in the field who is new to this project.
Goal: Explain how a Poisson problem becomes a nested iterative solver and which operations map to proposed photonic hardware.
Duration: 20 minutes plus technical appendix.
Primary research: Lee et al., Integrated photonic multigrid solver for partial differential equations, arXiv:2511.01005. Zhu et al. is related work only.

Key messages:
- Digital residual correction wraps PCG, whose preconditioner is a multigrid V-cycle.
- Only Richardson smoothing products are assigned to optics. The CPU owns all state, transfers, updates, scalar products, accurate residuals, and stopping decisions.
- Fixed operators act on changing local correction estimates. The optical vector is not the full PDE estimate.
- The browser is a 1D ideal teaching model. main.py is a distinct 2D noisy emulation inspired by Lee.
- Fresh measured residuals support convergence of these runs. MVM counts do not demonstrate hardware speedup.

Design: clean 16:9 white background, navy headings, teal digital operations, amber optical products, restrained purple for inter-level transfer. Editable native flowcharts, tables, charts, and equations. No decorative imagery. Repeat a compact method map with the current routine emphasized. Main slides reveal the computation progressively; appendix contains complete operators and details.

Tooling: the presentation skill's artifact-tool runtime and dependency loader are unavailable in this host. Use the installed mck-ppt-design engine as the PPTX container with native python-pptx objects for technical diagrams/charts, scoped dependencies in build/deps, and LibreOffice/Poppler rendering. Custom technical layouts are necessary to preserve complete algorithm branches and matrix dimensions; stock consulting layouts are not imposed on this content. Use readable font sizes instead of the skill's compact 14-point body default. No fabricated image placeholders.

Evidence: directly read the full 19-page Lee paper, all numerical source code, and browser core. Do not reuse numerical claims from the obsolete meeting guide. Collection scripts preserve solver source, add diagnostic observations, and record seeds/environment and source hashes.

Validation: source-to-slide mapping, independently recomputed true residuals, sparse operator dimension/Galerkin checks, source citations in notes, S3/S4 skill checks, rendered review of all slides, native shape/chart verification. Existing solver files remain unchanged.
