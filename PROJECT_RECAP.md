# Returning to the Photonic PDE Solver

A study guide for rebuilding your understanding of the mathematics, the papers,
and the code after a break.

## 1. What this project is trying to do

The central question is:

> Can low-precision photonic matrix multiplications help solve a discretized
> differential equation accurately while reducing high-precision digital work?

The project combines several numerical methods. Each has a different job:

| Component | Job |
| --- | --- |
| Finite differences | Turn a differential equation into a matrix equation |
| Conjugate gradient (CG) | Iteratively solve that matrix equation |
| Multigrid | Produce useful approximate corrections using multiple scales |
| Preconditioning | Use those corrections to help CG converge faster |
| Photonic multiplication model | Approximate selected matrix-vector products with quantization and noise |
| Residual correction | Use reliable digital residuals to recover accuracy |

Study them in that order. The nested solver becomes much easier to understand
once each component has a clear purpose.

## 2. What is currently in the repository?

| File | Current role |
| --- | --- |
| [smoother.py](smoother.py) | A 16-point 1D Poisson problem with a handwritten V-cycle, PCG, and outer correction loop |
| [main.py](main.py) | A 64 × 64 2D Poisson problem comparing plain CG, digital multigrid CG, and a noisy hybrid method |
| [web/index.html](web/index.html) | A 64-point 1D execution visualizer using ideal matrix multiplication labelled as optical |
| [pre.md](pre.md) | Earlier explanation of CG and preconditioning |
| [photonic_pde_meeting_guide.md](photonic_pde_meeting_guide.md) | Earlier meeting notes, including descriptions that do not match the current files |

**Keep these experiments separate while learning.** The webpage, `smoother.py`,
and `main.py` do not use the same problem size or all the same solver settings.

The meeting guide refers to `photonic_pde_solver.py`, which is absent from the
current repository. Its reported results should not be treated as results from
the current scripts.

## 3. Start with the physical problem

Imagine a rod with temperature fixed at both ends and heat generated inside.
We want its temperature at every position after it reaches equilibrium.

The problem in `smoother.py` is:

$$
-u''(s)=1,\qquad u(0)=100,\qquad u(1)=0.
$$

- **\(s\)** is position along the rod.
- **\(u(s)\)** is the unknown temperature.
- **\(u''(s)\)** describes how the temperature gradient changes with position.
- **The right-hand side, 1,** represents a uniform source in this model.
- **The boundary conditions** fix the temperatures at the two endpoints.

This 1D example is an ordinary differential boundary-value problem. It teaches
the numerical machinery used for the 2D Poisson PDE:

$$
-\left(
\frac{\partial^2u}{\partial s^2}
+\frac{\partial^2u}{\partial t^2}
\right)=f(s,t).
$$

Here, both \(s\) and \(t\) are spatial coordinates. In electrostatics, \(u\)
represents electric potential and the source is related to charge density.

`main.py` uses positive and negative source strips with zero values at the outer
boundary. The strips are prescribed sources, rather than internal boundaries
whose potentials are fixed.

> Solver iterations are successive guesses at an equilibrium solution. They
> are not physical time steps.

## 4. From the differential equation to a matrix

### 4.1 Replace a continuous function with grid values

A computer stores finitely many numbers. Choose interior grid points separated
by a distance \(h\), and store an unknown value \(u_i\) at each point.

Approximate the second derivative using neighbouring values:

$$
-u''(s_i)\approx\frac{2u_i-u_{i-1}-u_{i+1}}{h^2}.
$$

Each interior point now contributes one linear equation. Together they form:

$$
A\mathbf{x}=\mathbf{b}.
$$

| Symbol | Meaning |
| --- | --- |
| \(A\) | The rules coupling each grid point to its neighbours |
| \(\mathbf{x}\) | The unknown interior values of the solution |
| \(\mathbf{b}\) | Sources plus contributions from known boundary values |

### 4.2 A complete three-point example

For a small teaching example, use three interior points, **zero values at both
endpoints**, and source 1. These boundary values differ from `smoother.py` to
keep the example simple.

The spacing is \(h=1/4\), so:

```text
     [ 2  -1   0 ] [ x₁ ]   [ 1 ]
16 × [-1   2  -1 ] [ x₂ ] = [ 1 ]
     [ 0  -1   2 ] [ x₃ ]   [ 1 ]
```

The solution is:

```text
x₁ = 3/32
x₂ = 1/8
x₃ = 3/32
```

For example, the first equation checks out:

$$
16\left(2\cdot\frac{3}{32}-\frac18\right)=1.
$$

That is already a numerical Poisson solve.

### 4.3 How boundary conditions enter

When an endpoint value is nonzero, its contribution moves to the right-hand
side. The first interior equation is:

$$
\frac{2u_1-u_0-u_2}{h^2}=f_1.
$$

Since \(u_0\) is known:

$$
\frac{2u_1-u_2}{h^2}=f_1+\frac{u_0}{h^2}.
$$

This is what `build_b()` in `smoother.py` implements.

### 4.4 What changes in 2D?

Each interior point couples to four neighbours:

$$
4u_{i,j}-u_{i-1,j}-u_{i+1,j}-u_{i,j-1}-u_{i,j+1}
=h^2f_{i,j}.
$$

Flatten the 2D grid into a vector, and this again becomes \(A\mathbf{x}=\mathbf b\).
Most matrix entries are zero because only neighbours interact. This makes the
matrix **sparse**.

`main.py` uses an unscaled stencil with diagonal 4 and neighbour coefficients
−1. Its supplied `b` therefore represents the right-hand side in that stencil
scaling; physical units require a consistent choice of spacing and source scale.

## 5. Residual versus error

This distinction connects almost everything that follows.

Let \(\mathbf{x}_*\) be the exact solution of the **discrete matrix system**,
and let \(\mathbf{x}\) be our current guess.

The solution error is:

$$
\mathbf e=\mathbf{x}_*-\mathbf{x}.
$$

The residual is:

$$
\mathbf r=\mathbf b-A\mathbf{x}.
$$

| Quantity | What it tells us | Can we normally compute it? |
| --- | --- | --- |
| Error \(\mathbf e\) | How far the guess is from the exact discrete solution | No: the exact solution is unknown |
| Residual \(\mathbf r\) | How badly the guess violates the matrix equations | Yes |

Their connection follows directly from \(A\mathbf{x}_*=\mathbf b\):

$$
A\mathbf e
=A(\mathbf{x}_*-\mathbf{x})
=\mathbf b-A\mathbf{x}
=\mathbf r.
$$

> Solving \(A\mathbf e=\mathbf r\) finds the correction needed by the current
> guess.

If we could solve that equation exactly, adding the correction would finish:

$$
\mathbf{x}+\mathbf e=\mathbf{x}_*.
$$

In practice, we compute cheaper approximate corrections and repeat.

### Measuring convergence

The scripts use a relative residual criterion:

$$
\frac{\|\mathbf b-A\mathbf{x}\|_2}{\|\mathbf b\|_2}.
$$

A small value means the discrete equations are satisfied closely. Two further
questions remain distinct:

1. How does residual size translate into solution error? This depends on conditioning.
2. How closely does the discrete solution approximate the continuous problem?
   This depends on discretization, grid resolution, and the model.

## 6. Richardson iteration and smoothing

Richardson iteration updates a guess using its residual:

$$
\mathbf{x}_{k+1}
=\mathbf{x}_k+\omega(\mathbf b-A\mathbf{x}_k).
$$

Read this as:

1. Compute the equation mismatch.
2. Scale it by a chosen weight \(\omega\).
3. Add it to the guess.

The error evolves according to:

$$
\mathbf e_{k+1}=(I-\omega A)\mathbf e_k.
$$

If an error component lies along an eigenvector with eigenvalue \(\lambda\),
its amplitude is multiplied by:

$$
1-\omega\lambda.
$$

For these Poisson matrices and the chosen weights, rapidly oscillating error
components shrink quickly. Slowly varying components shrink slowly.

This is why Richardson is useful as a **smoother**. It removes jaggedness from
the error, but can be slow at removing broad, smooth error.

The scripts choose \(\omega\) using an estimate of the largest eigenvalue.
`main.py` uses power iteration; `smoother.py` uses a sparse eigenvalue routine.

## 7. Multigrid: correcting error at different scales

Smooth error left on a fine grid can often be represented in a much smaller
space. Multigrid uses that space to find a correction cheaply.

### A V-cycle, step by step

1. **Pre-smooth:** improve the current correction estimate.
2. **Compute a residual:** measure what remains unsatisfied.
3. **Restrict:** map that residual into a coarse space.
4. **Solve on the coarse level:** compute a coarse correction, recursively if needed.
5. **Prolong:** map the coarse correction back and add it.
6. **Post-smooth, if configured:** improve the result after interpolation.

The transfer operators are:

$$
\mathbf r_c=R\mathbf r,
\qquad
\mathbf e\leftarrow\mathbf e+P\mathbf e_c.
$$

- \(R\): restriction, from fine residuals to coarse residuals.
- \(P\): prolongation, from coarse corrections to fine corrections.
- \(A_c=RAP\): the coarse operator in this Galerkin construction.

Your PyAMG setup uses **algebraic multigrid**. It constructs coarse spaces from
the matrix structure; they need not be literal grids made by selecting every
second point.

One V-cycle returns an approximate correction. It does not need to solve the
whole problem to the final tolerance.

## 8. Conjugate gradient: the main iterative solver

For a symmetric positive-definite matrix \(A\), solving the system is equivalent
to minimizing a quadratic function:

$$
\phi(\mathbf{x})
=\frac12\mathbf{x}^TA\mathbf{x}-\mathbf b^T\mathbf{x}.
$$

Its gradient is:

$$
\nabla\phi(\mathbf{x})=A\mathbf{x}-\mathbf b=-\mathbf r.
$$

So the residual is the negative gradient. This connects linear solving to
gradient descent.

CG chooses directions that are conjugate with respect to \(A\):

$$
\mathbf p_i^TA\mathbf p_j=0\qquad(i\ne j).
$$

In exact arithmetic, this lets later steps preserve minimization already
performed along earlier directions.

Each step has two decisions:

- **Direction:** which vector \(\mathbf p\) to move along.
- **Step length:** how far to move, represented by \(\alpha\).

For a deeper treatment, read the quadratic-form, steepest-descent,
conjugate-direction, and preconditioning sections of
[Shewchuk’s illustrated CG tutorial](https://www.cs.cmu.edu/~quake-papers/painless-conjugate-gradient.pdf).

## 9. Preconditioning: how multigrid helps CG

A good preconditioner cheaply estimates the correction:

$$
\mathbf z\approx A^{-1}\mathbf r.
$$

Your project computes this estimate with a V-cycle:

```python
z = v_cycle(0, r)
```

The roles are:

> Multigrid produces approximate corrections. PCG uses them to construct
> search directions and choose step lengths.

There is no need to build an explicit inverse matrix.

### A notation trap

Some explanations call a matrix approximating \(A\) the preconditioner \(M\),
then apply \(M^{-1}\). SciPy’s `cg(..., M=...)` instead expects an operation
that approximates applying \(A^{-1}\).

In your code, the operation passed to SciPy is a V-cycle. Its meaning is
“approximately solve for a correction.”

### The hybrid method needs a theoretical caveat

Standard PCG assumes a fixed symmetric positive-definite preconditioner.
Quantization and random noise make the hybrid operation nonlinear or variable,
and its asymmetric smoothing does not supply the usual symmetry guarantee.

The current hybrid run converges empirically. The ordinary PCG convergence
guarantees do not automatically apply to it.

See [SciPy’s CG documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.cg.html)
for the solver’s matrix and preconditioner requirements.

## 10. Where photonic computation enters

Richardson smoothing repeatedly needs a matrix-vector product:

$$
\mathbf y=A\mathbf v.
$$

The hybrid approach substitutes an approximate photonic operation for selected
products inside the smoother.

In `main.py`, `noisy_mvm()` is a software model. It:

1. Finds the maximum absolute input value to set a scale.
2. Normalizes and quantizes the input using signed levels based on 127.
3. Multiplies using the matrix scaled by 1/4.
4. Adds Gaussian noise with standard deviation 0.045 in that normalized calculation.
5. Restores the output scale.

All of this currently runs on the computer. It models selected properties of
an analog multiplier; it is not a calibrated hardware simulation.

The following work remains digital in `main.py`:

- CG’s main matrix-vector products.
- Reliable residual evaluation.
- Restriction and prolongation.
- The coarse direct solve.
- Vector additions and scalar products.
- Solver control and stopping decisions.

## 11. Residual correction: recovering accuracy

A low-precision inner computation may produce a useful correction without
reaching the final accuracy on its own.

The outer loop repeats:

$$
\mathbf r=\mathbf b-A\mathbf{x},
$$

$$
A\boldsymbol\delta\approx\mathbf r,
$$

$$
\mathbf{x}\leftarrow\mathbf{x}+\boldsymbol\delta.
$$

The residual is recomputed digitally from the full solution estimate. The inner
solver then approximately solves a new correction problem.

Useful corrections can progressively improve accuracy beyond that of a single
low-precision solve. This requires the corrections to reduce the remaining
error sufficiently; convergence is not automatic for arbitrary noise.

### The complete nesting in `main.py`

```text
Outer residual correction
  │
  ├─ Compute a reliable digital residual: r = b − A x
  │
  ├─ Approximately solve A δ = r using short PCG runs
  │    │
  │    └─ Apply a multigrid preconditioner
  │         │
  │         ├─ Noisy Richardson pre-smoothing
  │         ├─ Digital residual and restriction
  │         ├─ Digital coarse solve
  │         └─ Digital prolongation and correction
  │
  └─ Update the full estimate: x ← x + δ
```

The hybrid configuration uses four pre-sweeps and no post-smoothing. The digital
baseline uses two pre-sweeps and two post-sweeps.

## 12. Reading the multigrid paper

**Paper:** Timoteo Lee et al.,
[*Integrated photonic multigrid solver for partial differential equations*](https://arxiv.org/pdf/2511.01005).

This paper matches the architecture and settings referenced by `main.py`:
photonic smoothing inside multigrid, multigrid inside a Krylov solver, and
digital residual iteration for precision recovery.

### Reading order

1. **Figure 1:** identify the problem, multigrid hierarchy, and photonic operation.
2. **Figure 2 and the mixed-precision method:** understand how the solver components cooperate.
3. **The Poisson capacitor example:** connect the experiment to `main.py`.
4. **Methods:** examine smoothing, the precision model, residual iteration, and operation counting.

### Questions to answer while reading

- Which matrix-vector products are photonic?
- Which products and residuals remain digital?
- What does each V-cycle return to the main solver?
- How is high final accuracy assessed?
- Which results use hardware, and which use emulation?
- What costs are included in the reported performance metric?

Keep the paper’s measurements separate from your local simulation results.

## 13. Reading the coherent-processor paper

**Paper:** Zheyuan Zhu et al.,
[*Coherent General-Purpose Photonic Matrix Processor*](https://pubs.acs.org/doi/10.1021/acsphotonics.3c01694),
ACS Photonics 11, 1189–1196 (2024).

Read this after understanding the multigrid architecture. It shifts attention
toward a programmable photonic processor: coherent signed multiplication,
electronic memory and reconfiguration, and error management. Its supporting
information covers Jacobi and Richardson methods with residual correction.

### Questions for comparing the papers

| Question | What to identify |
| --- | --- |
| What numerical method drives the PDE solve? | The update rule and stopping criterion |
| What operation does the optical core perform? | Its matrix/vector inputs and output |
| How are matrix entries supplied? | Stored weights or electronically streamed operands |
| How are signs represented? | The optical encoding and detection mechanism |
| How is precision recovered? | The digital correction strategy |
| What limits performance? | Conversion, communication, memory, noise, and optical computation |

Compare the numerical algorithms and the hardware interfaces separately. They
are related questions, but understanding one does not settle the other.

## 14. What the current scripts actually demonstrate

### `main.py`: verified run

One run in the existing `.venv` produced:

| Method | Counted digital MVMs | Simulated analog MVMs | Relative residual |
| --- | ---: | ---: | ---: |
| Plain CG | 148 | 0 | 7.8 × 10⁻¹¹ |
| Digital multigrid CG | 60 | 0 | 6.1 × 10⁻¹¹ |
| Noisy hybrid | 45 | 60 | 4.0 × 10⁻¹¹ |

All three residuals were below the requested tolerance of 10⁻¹⁰ in that run.
Exact counts may vary with the numerical environment and hierarchy setup.

The counters cover selected matrix-vector products. They exclude setup and
other work, including the cost of the coarse solve, transfers, and scalar/vector
operations. The printed ratio is not a measured wall-clock speedup.

### `smoother.py`: current final-check failure

The script computes a solution and reaches its plotting call, then fails at:

```python
r = b - A @ x
```

Earlier in the script, `A` was changed from one matrix into a list of matrices,
one for each multigrid level. The intended fine-grid residual expression is:

```python
r = b - A[0] @ x
```

This guide records the issue; it does not change the solver.

## 15. A clearer webpage structure

The existing page introduces several nested loops and hardware blocks at once.
The learning experience should introduce one concept at a time, then connect
them in a final execution view.

| Lesson | Main visual | Useful interaction |
| --- | --- | --- |
| 1. Physical problem | A rod, boundary values, and a source | Change the source and predict the solution shape |
| 2. Discretization | Grid points linked to matrix rows | Select a point and highlight its equation |
| 3. Residual and error | Current guess, reference solution, and mismatch | Move one value and inspect the affected equations |
| 4. Smoothing | Jagged and smooth error components | Apply one Richardson sweep |
| 5. Multigrid | Fine and coarse corrections | Follow one V-cycle |
| 6. CG and PCG | Search directions and convergence | Compare convergence with and without multigrid |
| 7. Photonic approximation | Input, quantization, noisy product | Compare ideal and noisy results |
| 8. Full experiment | Nested solver and measured counts | Reproduce a stated Python configuration |

Each lesson should contain:

- One main question.
- One equation introduced with its symbols defined.
- One focused interaction.
- A short interpretation of the result.
- A link to the corresponding code.

The current execution dashboard belongs near the end of this sequence. At that
point, its loops and variables will already have meaning.

## 16. Suggested study checkpoints

Work through these in order. Explain each answer in your own words before
moving on.

- [ ] Explain what the source and boundary conditions mean physically.
- [ ] Derive one finite-difference equation from the differential equation.
- [ ] Construct the three-point matrix example by hand.
- [ ] Explain the difference between residual and solution error.
- [ ] Derive why \(A\mathbf e=\mathbf r\).
- [ ] Perform one Richardson update by hand.
- [ ] Explain why smoothing treats different error components differently.
- [ ] Describe restriction, coarse correction, and prolongation.
- [ ] Explain the separate jobs of PCG and a multigrid V-cycle.
- [ ] Trace one call through the hybrid solver in `main.py`.
- [ ] Identify every operation replaced by the noisy multiplication model.
- [ ] Explain how digital residual correction can recover accuracy.
- [ ] Read the multigrid paper and map its components to the code.
- [ ] Read the coherent-processor paper and compare its hardware interface.
- [ ] Separate residual accuracy, PDE discretization accuracy, operation counts, and runtime.

**First checkpoint to master:** explain why \(A\mathbf e=\mathbf r\). This
identity is the foundation of the correction loops throughout the project.
