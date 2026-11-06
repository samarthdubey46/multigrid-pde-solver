## 1. Photonic multigrid for Poisson problems

20-minute technical discussion. The contribution is a working numerical emulation and an inspectable architecture demonstrator. No experimental photonic processor or measured hardware speedup is claimed. Primary paper: https://arxiv.org/pdf/2511.01005.

Sources: Project implementation inspired by Lee et al. (2025)

## 2. The paper assigns smoothing products to optics

Lee combines multigrid preconditioning with digital Krylov iteration and residual correction. The demonstrated Poisson case uses two AMG levels. Its optical core stores weights and computes smoothing products. We adopt that computational partition. Source: https://arxiv.org/pdf/2511.01005. The deck explains repository code rather than copying the paper figures.

Sources: Lee et al., arXiv:2511.01005, pp. 3–6, 15–16

## 3. Three implementations, different settings

Keep every later result attached to its implementation. The browser is based more closely on the 1D smoother.py algorithm but uses N=64. smoother.py currently reaches its solve output then raises a ValueError in the final residual expression because A is a list. No results here are attributed to that failing report. Paper: https://arxiv.org/pdf/2511.01005.

Sources: Lee et al.; main.py; web/index.html; smoother.py

## 4. The unknown vector stores sampled solution values

The teaching problem is a 1D Poisson boundary-value problem, mathematically an ODE reduction of the PDE. Interior unknowns only are in x. Known boundaries enter b. h=1/65. The analytic quadratic is also the exact discrete solution for this stencil up to floating-point error. Its samples are a reference, never solver input.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 5. The residual becomes the next correction problem

Let x* denote the exact discrete solution. Then A(x*−x)=b−Ax. We can measure r without knowing x*. PCG approximately solves for δ. Corrections change only interior values; boundary changes are zero. A small true residual certifies equations are closely satisfied, not by itself a universal solution-error bound.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; Lee Methods p. 16

## 6. One solver map connects all four routines

This is a call hierarchy, not four physical chips. Each routine returns to its caller. Subsequent slides expand these same four blocks. Only the product inside the last block is assigned to optics. V-cycle is an action approximating A inverse, not an explicitly stored inverse or matrix M.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 7. The CPU closes every optical smoothing loop

Functional hardware proposal for the browser. The CPU selects a level, retains e and g, and sends only e through shared DAC/modulator. Source illumination is not an extra numerical operation. Optical matrix weights act on the signed numerical representation; no specific signed encoding, sparse tiling, or physical switch is specified. Detector/ADC returns y, then CPU applies the Richardson update. CPU-only work does not require an extra trip through optics.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; web/README.md hardware mapping

## 8. A real smoothing request changes the local vector

Numbers from the actual second pre-sweep on level zero in the first browser V-cycle, rounded for display. First sweep sends a zero vector and returns zero, giving e=ωg. The browser retains this zero-input MVM in its counters. x remains zero throughout the first correction solve; only local e changes here. All vector excerpts use indices1–3 of64.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; zero-start event trace

## 9. The multigrid V-cycle

Actual browser schedule, 3 pre and3 post sweeps at each noncoarsest level. On entry initialize e_l=0. After pre-smoothing compute d_l=g_l−A_l e_l digitally, restrict g_next=R_l d_l, recurse. On return add P_l e_next to retained e_l and post-smooth. At the top return z=e0. AMG levels are algebraic spaces, not uniformly subsampled physical meshes. In main.py the hybrid schedule is a different two-level4/0 cycle.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 10. Smoothing and coarse correction

This is a controlled numerical teaching experiment using the stored browser operators, not a physical measurement. Choose an initial error sin(πt)+0.35sin(32πt), solve homogeneous error equation with three Richardson sweeps, apply the recursive coarse correction, then three post-sweeps. Display error profiles against zero. Norms are independently computed. The amplification relation follows directly from the Richardson update.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; derived.json controlled error experiment

## 11. PCG turns a V-cycle correction into a search step

The fixed RHS r is the outer residual for this PCG call. δ starts at zero. s is the residual of this correction problem. z is one V-cycle result. q=A0p is a high-precision CPU MVM, not the optical smoothing MVM. The ordering q before alpha is essential. The next slide completes the recurrence and stopping branches.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; PCG recurrence

## 12. PCG stopping and direction updates

Browser exact branch order: after δ and s updates compute ||s||/||r||. If below1e-2 returnδ. Otherwise compute another V-cycle, beta and direction update even on the final capped iteration, then the loop exits after20. The appendix records this detail. main.py instead calls SciPy CG with maxiter5 and rtol1e-12. Numerical breakdown is distinct from convergence.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; browser inner limit: 20 iterations

## 13. Outer correction and true-residual checks

Browser: outer loop at most10 corrections; tolerance1e-12; after the final correction it recomputes true residual and distinguishes converged/limit. main.py uses at most100 restarts, tolerance1e-10, and the run report recomputes final residual. Breakdown is a separate failure state. Fresh outer r is not a recycled inner residual. This is how correction quality is checked despite approximate inner products.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; main.py solve_with_restarts

## 14. The hierarchy is fixed while its vectors change

Setup creates all A,P,R and omega values. A_next=R A P and R=P transpose are verified against the stored browser matrices. Optical copies of A0,A1,A2 serve smoothing; CPU copies compute reliable level residuals. A3 is a CPU direct solve. P,R are only digital. All ten browser operators appear in the appendix with values and sparsity. Coarsest omega is stored but unused.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; Galerkin and transpose identities verified

## 15. Convergence of the ideal browser model

Reproduced the browser core without modifying it. Five outer corrections, ten top-level V-cycles,180 optical and111 digital calls, relative residual3.1704180357133085e-13. Plot left shows actual true residual history. Right shows final error against the analytic quadratic, not merely two visually overlapping solution curves. Counts include different matrix sizes and are not runtime weights.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; fresh zero-start execution

## 16. The separate 2D noisy experiment

Actual64×64 positive discrete Laplacian with zero exterior values and signed source strips at rows21 and42, columns16through47. These are source terms, not prescribed-potential internal boundaries. Coordinates and amplitudes use the code unscaled stencil units. Displayed center-column profile is taken from the full computed2D field. Independent sparse direct solution is used only as evaluation reference. Main source SHA and versions are in research/main-data.json.

Sources: main.py: original solver, observed by presentation/build/collect_python.py

## 17. Counted digital products in the 2D run

Plain148, digitalMG60, hybrid45 counted digital products; hybrid60 analog calls. Relative residuals independently observed: plain7.8e-11,digital6.1e-11,hybrid3.961e-11. Hybrid is69.6% fewer fine-grid digital products versusplain,25% versusdigitalMG. Excluded costs: setup,power iteration,P/R transfers,coarse spsolve, scalar/vector work, reporting residual,DAC/ADC,memory,calibration. Coarse matrix704×704 means excluded coarse cost can be material. No runtime or energy claim.

Sources: main.py: original solver, observed by presentation/build/collect_python.py; one controlled run, setup seed 0

## 18. Implemented behavior and open questions

Paper-inspired structure is implemented, not an exact hardware reproduction. main.py quantizes the input and adds fresh Gaussian output noise. It has no matrix quantization, physical encoding, averaging or timing. Browser uses ideal MVMs and a functional shared-converter diagram. Classical PCG assumptions are not guaranteed under noisy variable asymmetric preconditioning. Zhu related work supports coherent signed multiplication with digital memory/reconfiguration, not a claimed replacement for the current multigrid code. References: https://arxiv.org/pdf/2511.01005; https://doi.org/10.1021/acsphotonics.3c01694.

Sources: main.py: original solver, observed by presentation/build/collect_python.py; web/README.md; Lee Methods

## 19. Next validation: full computational cost

Close on the scientific contribution and next validation. The method works for the reported cases. A next experiment should retain identical matrices and compare calibrated noisy MVM/preconditioner variants over repeated seeds, use independently recomputed residuals, and include coarse factorization, transfers, memory/conversion overhead in time/energy accounting. Do not promise an outcome. Main talk ends here; the following slides are technical backup.

Sources: main.py: original solver, observed by presentation/build/collect_python.py; web/README.md

## 20. Complete recurrence and termination conditions

Exact algebraic recurrence of the browser core. Index k counts completed PCG iterations. rho_new overwrites rho after beta. At the capped final iteration, the source still computes its next V-cycle and direction before returning. Breakdown checks nonfinite alpha and positive pTq. Outer loop distinguishes convergence and limit.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 21. Recursive V-cycle and smoothing pseudocode

V(l,g) returns a local correction. R_l=P_l transpose. The coarse solve uses elimination, not an explicit inverse. CPU computes d and all transfer products. e starts at zero only on V-cycle entry; post-smoothing starts from the corrected value. Main2D cycle differs and is shown later.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 22. Fine operators A₀ and A₁

Actual stored matrices. Sparsity panels show every nonzero; tables are labeled excerpts, not complete matrices. A0=h^-2 tridiag(−1,2,−1), h=1/65. All entries are retained in embedded browser CSR data.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 23. Coarse operators A₂ and A₃

Complete numerical matrices, rounded to3decimals. A2 has22 nonzeros, A3 has7. Original sparse matrices remain full precision. A3 direct solve is CPU-only. No inverse is formed.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 24. Transfer operators P₀ and R₀

Every nonzero is shown in the sparsity views. Selected numerical entries below are excerpts. R=P transpose exactly in stored data. These operators do not change during the solve, and both matrix-vector operations are digital.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 25. Transfer operators P₁ and R₁

Every nonzero is shown in the sparsity views. Selected numerical entries below are excerpts. R=P transpose exactly in stored data. These operators do not change during the solve, and both matrix-vector operations are digital.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 26. Transfer operators P₂ and R₂

Complete final transfer pair rounded to4decimals. This is an algebraically constructed interpolation matrix, not simple averaging or selection of every nth physical sample.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data

## 27. The 2D experiment uses four fixed sparse matrices

All four stored matrices of main.py: A,P,R,Ac. Matrix A has4096rows,20224nnz. P4096x704 with10116nnz, R transpose, Ac704square6096nnz. A=I64 kronT64 +T64 kronI64 with T tridiag−1,2,−1. The occupancy views bin sparse indices into64x64 cells for legibility; a colored bin indicates at least one nonzero, not a literal matrix entry. Identity is notation, not a separately allocated solver matrix.

Sources: main.py: original solver, observed by presentation/build/collect_python.py

## 28. Settings and counter definitions

main.py uses SciPy CG with inner rtol1e-12 and maximum5steps in each outer restart, tolerance1e-10 maximum100restarts. Browser inner rtol1e-2maximum20,outer1e-12maximum10. main counter includes fineA exact/noisy wrappers only; excludes setup/diagnostics/transfers/coarsesolve. Browser countsdigital A,R,P, plus opticalA and convertercalls. Neither is a complete hardware cost model. main.py ignores info codes; reported convergence independently checked.

Sources: main.py; web/index.html; source-level review

## 29. Convergence theory and observed results

SciPy CG requires Hermitian positive definiteA and a Hermitian positive definite preconditioner. The standard fixed linear SPD-preconditioner argument doesnot transfer automatically to this noisy, quantized, asymmetric action. This run converges empirically. A nextcomparison should include flexibleKrylov formulations and multiple noise realizations. https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.cg.html . Residual-error relation is exact for invertibleA; conditioning and discretization remain distinct.

Sources: SciPy CG documentation; main.py; web/index.html

## 30. Related work: Zhu’s coherent processor

Relatedwork only. Verified publisherabstract describes coherent analogue cores that perform signed multiplication, digital electronics for memory/reconfigurability, and error management for finite-difference PDEs. The supplementary-information listing explicitly covers fixed-point Richardson and Jacobi with residuecorrection. We do not claim a reproduction of that hardware, exact PDE geometry, bitdepth, or iteration schedule. Source:https://doi.org/10.1021/acsphotonics.3c01694. Fullpaywalledarticle wasnotused for detailednumericalclaims.

Sources: Zhu et al., ACS Photonics 11, 1189–1196 (2024)

## 31. The actual two-level cycle in main.py

Exact main.py V-cycle. smooth(g,mvm,pre) starts e=omega*g, then applies pre-1 updates. The residual d=g−A e is digital. RestrictionR, coarse spsolveAc, and prolongationP are digital. For digital2/2, post smoothing is applied as a correction to the existing e: e+=smooth(g−A e,exact_mvm,2). This equals two Richardson post-updates in exact arithmetic. Hybrid4/0returnswithoutpost. PlainCG anddigitalMGCGsolveAx=bdirectly; onlyhybridusesouterrestartscorrectionloop.

Sources: main.py: original solver, observed by presentation/build/collect_python.py

## 32. Setup constructs operators before iteration starts

Hierarchy is constructed before reported solver counters. PyAMG smoothed aggregation formsP,R and Galerkincoarseoperators. Browser ships these matrices asCSRarrays; allsetupiscompletebeforevisualized solve. Source smoother.py computesweightsbyeigsh. main.py estimatesfineoperator spectralradiusby30poweriterationsusing itsseededgenerator. Stored browsercoarsestomega isunusedbecauselevel3directsolve. Setup isnot countedinthe reportedMVMs.

Sources: web/index.html: PhotonicSolver numerical core and embedded sparse matrix data; main.py PyAMG setup

## 33. True residuals contract across noisy restarts

The histogram is not reconstructed from CG recursive residuals. At each accumulatedoutercorrection,weindependentlycompute||b−Ax||/||b||withthesparseA. FourcorrectioncallswithfiveCGstepseachproduce20Vcycles and60analogcalls. Theouterloopthenchecksconvergence. Monitoring MVMs areanalysisdiagnostics andnotinsertedintotheoriginalcounter. Plot usesa truelogarithmicverticalaxis.

Sources: main.py: original solver, observed by presentation/build/collect_python.py; independently recomputed residual history