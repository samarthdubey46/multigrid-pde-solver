# Photonic PDE Solver — Meeting Guide

## 1. The whole project in one paragraph

A PDE is first discretized into a sparse linear system `A x = b`. The high-precision digital solver is conjugate gradient (CG). A multigrid V-cycle acts as a preconditioner, so CG reaches the solution in fewer iterations. The expensive repeated operation inside the multigrid smoother is a matrix-vector multiplication `A_l @ x`; the old paper sends this operation to a low-precision photonic processor. Restriction, prolongation, scalar products, the coarse solve, and reliable residual calculations remain digital. High-precision residual iteration repeatedly corrects the error accumulated by analog quantization and noise.

The claim is therefore **not** “light directly solves a PDE.” The honest claim is: **a physical optical system performs selected matrix-vector products inside a hybrid numerical PDE solver.**

---

## 2. Audit of the uploaded `smoother.py`

The uploaded script is a good algorithmic skeleton, but it should not be described as a 2D heat-transfer simulation.

It solves

\[
-\frac{d^2u}{dx^2}=1, \qquad u(0)=100,\quad u(1)=0,
\]

on 1,000 interior points. This can be interpreted as 1D steady heat conduction with uniform volumetric heating, or simply as a 1D Poisson boundary-value problem.

### What was already present

- Finite-difference matrix construction.
- Smoothed-aggregation algebraic multigrid through PyAMG.
- Richardson smoothing:

\[
x_{k+1}=x_k+\omega(b-Ax_k).
\]

- A recursive V-cycle.
- Hand-written preconditioned conjugate gradient.
- Outer residual correction: compute a true residual, approximately solve for a correction, and add it to the current solution.

### What was missing from the photonic paper

- The problem was 1D, while the paper’s capacitor example is 2D.
- `A @ x` in the smoother was exact floating-point multiplication, not photonic.
- No fixed-point quantization.
- No analog/noisy MVM model.
- The V-cycle used three pre- and three post-sweeps; the hybrid solver in the paper uses four pre-sweeps and no post-smoothing.
- No accounting of digital versus photonic MVMs.
- No hardware parameters such as bit depth, noise, or repeated optical measurements.
- The script printed the full 1,000-element solution and returned the zero-based loop index as its iteration count.

---

## 3. From a 2D PDE to `A x = b`

For the old paper’s electrostatic example,

\[
\nabla^2u(y,z)=f(y,z)=\frac{\rho}{\epsilon}.
\]

On a square grid with spacing `h`, the central finite-difference approximation is

\[
\frac{u_{i+1,j}+u_{i-1,j}+u_{i,j+1}+u_{i,j-1}-4u_{i,j}}{h^2}=f_{i,j}.
\]

After multiplying by `h²`, every interior point produces one linear equation. Flattening `(i,j)` into a single index produces

\[
A\mathbf{u}=\mathbf{b}.
\]

For the positive-definite sign convention used by CG, `A` has approximately five nonzero entries per row:

- diagonal: `+4`;
- four neighbours: `−1`;
- fewer neighbours next to a Dirichlet boundary.

The same operator describes steady heat conduction. Only the physical meanings change:

| Electrostatics | Heat conduction |
|---|---|
| `u`: electric potential | `u`: temperature |
| `f`: charge density / permittivity | `f`: heat generation / conductivity |
| `E = −∇u` | heat flux `q = −k∇u` |

The hardware receives `A` and vectors; it does not know whether they came from heat, charge, quantum mechanics, or a particularly annoyed fluid.

---

## 4. Why Richardson is a smoother

Let `x*` be the exact solution and define the error

\[
e_k=x^*-x_k.
\]

Because `b=Ax*`, Richardson iteration gives

\[
e_{k+1}=(I-\omega A)e_k.
\]

Expand the error in eigenvectors `v_i` of `A`:

\[
e_k=\sum_i c_i^{(k)}v_i, \qquad Av_i=\lambda_i v_i.
\]

Then every eigenmode evolves independently:

\[
c_i^{(k+1)}=(1-\omega\lambda_i)c_i^{(k)}.
\]

For the discrete Laplacian, high-spatial-frequency modes are associated with larger eigenvalues. With a suitable `ω`, their amplification factor has small magnitude, so they decay rapidly. Smooth, low-frequency error decays slowly on the fine grid.

Multigrid’s trick is to restrict that smooth error to a coarser grid. On the coarse grid it appears more oscillatory relative to the larger grid spacing and becomes easier to remove.

The paper uses approximately

\[
\omega\approx\frac{1}{\rho(A)},
\]

where `ρ(A)` is estimated by power iteration.

---

## 5. Conjugate gradient from first principles

### 5.1 When CG applies

Standard CG requires `A` to be symmetric positive definite (SPD):

\[
A=A^T, \qquad y^TAy>0\quad\text{for all }y\ne0.
\]

The positive discrete Laplacian with Dirichlet boundaries is SPD.

### 5.2 Solving a linear system is minimizing a quadratic

Define

\[
\phi(x)=\frac12x^TAx-b^Tx.
\]

Its gradient is

\[
\nabla\phi(x)=Ax-b=-r,
\]

where

\[
r=b-Ax
\]

is the residual. Therefore the minimum of `φ` satisfies `Ax=b`.

### 5.3 Choosing the step length

Move from `x_k` along direction `p_k`:

\[
x_{k+1}=x_k+\alpha_kp_k.
\]

Minimize `φ(x_k+αp_k)` with respect to `α`:

\[
\frac{d\phi}{d\alpha}=-p_k^Tr_k+\alpha p_k^TAp_k=0.
\]

Hence

\[
\alpha_k=\frac{p_k^Tr_k}{p_k^TAp_k}.
\]

For ordinary CG, the recurrence makes `p_k^T r_k=r_k^Tr_k`, giving the familiar formula

\[
\alpha_k=\frac{r_k^Tr_k}{p_k^TAp_k}.
\]

### 5.4 Why the directions are “conjugate”

CG constructs directions satisfying

\[
p_i^TAp_j=0 \qquad (i\ne j).
\]

These directions are orthogonal under the `A`-inner product. Once CG minimizes the quadratic along one direction, later conjugate directions do not undo that correction. In exact arithmetic, an `n×n` SPD problem converges in at most `n` iterations. In practice it often converges much earlier when eigenvalues are clustered.

### 5.5 The basic CG recurrence

\[
\begin{aligned}
r_0 &= b-Ax_0,\\
p_0 &= r_0,\\
\alpha_k &= \frac{r_k^Tr_k}{p_k^TAp_k},\\
x_{k+1} &= x_k+\alpha_kp_k,\\
r_{k+1} &= r_k-\alpha_kAp_k,\\
\beta_k &= \frac{r_{k+1}^Tr_{k+1}}{r_k^Tr_k},\\
p_{k+1} &= r_{k+1}+\beta_kp_k.
\end{aligned}
\]

---

## 6. What preconditioning changes

If the eigenvalues of `A` span a very wide range, the quadratic is highly elongated and CG needs many steps. A preconditioner approximately applies the inverse of `A`:

\[
z_k=M^{-1}r_k\approx A^{-1}r_k.
\]

In this project, one multigrid V-cycle computes `z_k`. PCG then uses

\[
\begin{aligned}
\alpha_k &= \frac{r_k^Tz_k}{p_k^TAp_k},\\
\beta_k &= \frac{r_{k+1}^Tz_{k+1}}{r_k^Tz_k},\\
p_{k+1} &= z_{k+1}+\beta_kp_k.
\end{aligned}
\]

The notation in papers can be slippery. Some authors call the approximate inverse itself `M`; others call the matrix being inverted `M`. In the code, the meaning is unambiguous:

```python
z = v_cycle(r)
```

so `v_cycle` acts like `A⁻¹` on the residual.

### Important theoretical caveat

Standard PCG assumes the preconditioner is fixed, symmetric, and positive definite. A stochastic photonic MVM makes the effective preconditioner vary from call to call, and four pre-sweeps with no post-smoothing make the V-cycle asymmetric.

The paper shows that CG still works empirically, but the standard proof no longer applies cleanly. A serious follow-up should compare:

- restarted PCG;
- flexible CG where appropriate;
- FGMRES, which is designed for variable and possibly nonsymmetric preconditioners.

This is a strong discussion point for the meeting.

---

## 7. Residual iteration: how low precision reaches high accuracy

Suppose a low-precision solver produces an approximate solution but eventually stagnates. Compute the true high-precision residual

\[
r=b-Ax.
\]

The exact remaining error `e=x*−x` obeys

\[
Ae=r.
\]

Therefore:

1. Compute `r=b−Ax` digitally in high precision.
2. Approximately solve `Ae=r` using the low-precision photonic-preconditioned solver.
3. Update `x←x+e`.
4. Recompute a fresh high-precision residual.
5. Repeat until the desired accuracy is reached.

The low-precision solver does not need to produce the final answer in one shot. It only needs to make each correction useful.

---

## 8. Old paper: exactly where the photonic hardware enters

### Photonic operation

Only matrix-vector products inside Richardson smoothing are offloaded:

\[
A_lx_k \quad\longrightarrow\quad \text{photonic MVM}.
\]

### Digital operations

- CG’s fine-grid `A p`.
- Reliable residual `b−Ax`.
- Vector additions and scalar products.
- Restriction `Rr` and prolongation `Pe`.
- Coarsest-grid direct solve.
- Residual iteration.

### Experimental core

- 9×3 integrated optical crossbar.
- Electro-absorption modulators encode input amplitudes.
- Tunable absorbers store matrix weights for in-memory computing.
- Photodetectors read accumulated products.
- DAC/ADC interfaces operate at 2 GS/s.
- Experimental matrix weights are rounded to 4-bit and inputs to 8-bit.
- Because the amplified-spontaneous-emission source is noisy, experimental operations are repeated 256 times and averaged.

### Paper’s digital noisy emulation

For the LQCD study, the paper rescales matrix and input values to `[-1,1]`, discretizes to 8-bit, adds Gaussian noise with standard deviation `0.045`, performs the MVM, and rescales the result.

The exact location and correlation structure of every experimental noise contribution are not fully specified in the manuscript. The new simulation therefore exposes the noise model as a replaceable component instead of pretending it is calibrated hardware.

---

## 9. What the extended simulation implements

File: `photonic_pde_solver.py`

### Problem

- 2D parallel-plate Poisson problem.
- `63×63 = 3,969` interior unknowns.
- Five-point positive discrete Laplacian.
- Homogeneous Dirichlet outer boundary.

### Multigrid

- PyAMG smoothed-aggregation hierarchy.
- Paper-style spectral-radius estimate by power iteration.
- Digital baseline: two pre- and two post-Richardson sweeps.
- Photonic version: four pre-sweeps and zero post-sweeps.
- Digital restriction, prolongation, residual evaluation, and coarse solve.

### Photonic MVM model

- Separate matrix and input bit depths.
- Normalization to `[-1,1]`.
- Signed uniform fixed-point quantization.
- Configurable detector-output Gaussian noise.
- Configurable averaging count.
- Reproducible random seed.

### Solver safeguards and measurements

- Explicit PCG recurrence for teaching.
- High-precision outer residual refinement.
- Restart if a noisy preconditioner produces a non-descent direction.
- Separate digital and photonic MVM counters.
- Reference solution and relative solution error.
- Source, solution, and convergence plot.

### One verified run

| Method | Final relative residual | Relative solution error | Digital MVMs | Photonic MVMs |
|---|---:|---:|---:|---:|
| Digital MG-PCG | `7.42×10⁻¹⁰` | `7.78×10⁻¹¹` | 193 | 0 |
| Ideal 8-bit photonic + RI | `3.33×10⁻¹⁰` | `1.18×10⁻¹¹` | 107 | 288 |
| Noisy 8-bit photonic + RI | `5.71×10⁻¹⁰` | `1.52×10⁻¹¹` | 119 | 324 |

Do not present these counts as measured speedup. They are algorithmic operation counts from one seeded simulation. A credible speed/energy claim must include conversion, memory, communication, optical averaging, and calibration overhead.

### Run it

```bash
python -m pip install numpy scipy matplotlib pyamg
MPLBACKEND=Agg python photonic_pde_solver.py
```

---

## 10. New paper: coherent general-purpose photonic MPU

The new PDF is:

**Zhu et al., “Coherent General-Purpose Photonic Matrix Processor,” ACS Photonics 11, 1189–1196 (2024).**

It is related to the old paper but uses a different hardware philosophy.

### 10.1 Signed multiplication by coherent detection

Two optical fields encode a matrix value and vector value. Balanced detection subtracts the intensities of the constructive and destructive outputs:

\[
V\propto |E_A+E_X|^2-|E_A-E_X|^2
=2\operatorname{Re}(E_A^*E_X).
\]

The phase can represent positive and negative signs, so the core naturally performs signed multiplication.

### 10.2 Multiple dimensions encode a dot product

The fields are superpositions of orthogonal modes:

\[
E_A=\sum_n A_{mn}\Psi_n, \qquad E_X=\sum_nX_n\Psi_n,
\]

with `Ψ_i·Ψ_j=δ_ij`. Detection accumulates contributions from matching modes, producing

\[
y_m=\sum_nA_{mn}X_n.
\]

The experiment uses wavelength-division multiplexing and in-phase/quadrature modulation. TDM and multiple cores extend the operation beyond a physical 2×2 core.

### 10.3 PDE example

The paper solves an electrostatic Poisson equation on a `64×64` grid:

- `4,096` unknowns;
- a `4096×4096` Laplacian;
- `19,162` nonzero entries;
- two point charges;
- a grounded conducting circular shell;
- zero-potential outer boundaries.

Split the Laplacian into its diagonal and off-diagonal parts:

\[
L=\operatorname{diag}(d)+U.
\]

Weighted Jacobi updates

\[
V^{(k)}=omega d^{-1}\odot\left(r-UV^{(k-1)}\right)
+(1-\omega)V^{(k-1)},
\]

with `ω=0.9`.

Only the sparse-dense product `U V` is photonic. Elementwise multiplication, addition, memory lookup, iteration control, and residual correction remain electronic.

### 10.4 CSR mapping to hardware

For each matrix row:

1. Store nonzero values `U_i` and their column indices `j[i]` in CSR form.
2. Stream `U_i` through a DAC to the signal port.
3. Use `j[i]` to fetch the matching vector entry `V_{j[i]}` from FPGA block memory.
4. Stream that vector value to the local-oscillator port.
5. Coherently multiply and accumulate the products.
6. A row-delimiter pulse resets the accumulator and outputs one result entry.

Because a five-point Laplacian has only four off-diagonal neighbours, four wavelengths could encode the nonzeros in one row, while parallel cores process multiple rows.

### 10.5 Precision management

- PDE firmware supports signed 3-bit sparse coefficients.
- Weighted Jacobi uses residual correction every five iterations.
- After 500 iterations, the reported residual norm is `0.024`, corresponding to better than 5.3-bit solution precision.
- For higher precision, the backend decomposes operands in base `β=3`:

\[
A=\beta A_H+A_L,\qquad X=\beta X_H+X_L,
\]

and combines four photonic partial products:

\[
AX=\beta^2A_HX_H+\beta A_HX_L+\beta A_LX_H+A_LX_L.
\]

This is essentially multi-digit fixed-point multiplication built around a low-precision optical core.

---

## 11. Old paper versus new paper

| Question | Old photonic multigrid paper | Zhu et al. coherent MPU paper |
|---|---|---|
| Main numerical method | CG/LOBPCG + multigrid preconditioner | Weighted Jacobi for PDE; Richardson for inversion |
| Optical operation | `A_l x` inside multigrid smoothing | Sparse `U V` inside Jacobi |
| Matrix handling | Weights stored in a photonic in-memory crossbar | Nonzero matrix entries dynamically streamed |
| Optical principle | Incoherent broadcast-and-weight crossbar | Coherent signed multiplication + balanced detection |
| Precision recovery | Digital residual iteration around Krylov solve | Residue update every few fixed-point iterations |
| Best conceptual contribution | Photonics as a multigrid preconditioner | General programmable photonic matrix processor |
| Current simulation status | Implemented approximately | Understood; exact reproduction is next |

The papers are complementary. The old paper gives the stronger numerical architecture; the new paper gives a more explicit programmable sparse-MVM hardware mapping.

---

## 12. A two-minute progress explanation

> My original script discretized a 1D Poisson problem and solved the resulting sparse system using a PyAMG V-cycle as a preconditioner for conjugate gradient. I have now separated the solver into high-precision digital and low-precision photonic parts and upgraded the physical example to a 2D parallel-plate Poisson problem.
>
> In the mixed-precision design, CG computes reliable residuals and scalar products digitally. One multigrid V-cycle approximately applies the inverse of the system matrix to the residual. Inside that V-cycle, Richardson smoothing repeatedly needs `A_l x`; those MVMs are replaced by a photonic model with signed 8-bit quantization and Gaussian noise with sigma 0.045, following the old paper’s emulation. The model uses the paper’s asymmetric four-pre-sweep V-cycle and outer high-precision residual refinement.
>
> In one seeded 63×63 run, the noisy photonic version reached a relative residual of about `5.7×10⁻¹⁰`, using 119 digital and 324 simulated photonic MVMs. This is not yet a hardware speedup claim because DAC/ADC, memory movement, and calibration are not modeled.
>
> I also studied the new coherent MPU paper. Unlike the fixed-weight crossbar, it streams CSR matrix nonzeros and selected vector entries through a coherent core, performs signed products by balanced detection, and uses weighted Jacobi with digital residual correction every five iterations. My next step is to reproduce its exact 64×64 sparse-Jacobi experiment and then compare that hardware mapping with the multigrid-preconditioned architecture.

---

## 13. Questions your professor may ask

### “What exactly is optical?”

Only selected matrix-vector products. In the old architecture it is `A_l x` inside Richardson smoothing; in the new paper it is sparse `U V` inside weighted Jacobi.

### “Why not put the whole solver in optics?”

CG needs reliable dot products, recurrence coefficients, residuals, control flow, and memory updates. Analog photonics is strongest at massively parallel linear multiplication, not arbitrary high-precision logic.

### “Why multigrid if you already have CG?”

CG can struggle when the system has widely spread eigenvalues. Multigrid quickly approximates `A⁻¹r`, especially removing spatial error modes that are slow for the main solver. It improves the search direction and reduces outer iterations.

### “How does residual correction exceed hardware precision?”

A fresh high-precision residual describes the remaining error even when the approximate solution has accumulated low-precision drift. Repeatedly solving the residual equation adds successive corrections, so final accuracy is not limited to one analog solve’s bit depth.

### “Is your noise model physically accurate?”

Not yet. It follows the paper’s quantization and sigma value, but it treats the unspecified hardware noise as detector-output Gaussian noise. The next calibration should match measured NMSE, scale dependence, bias, correlations, saturation, and averaging.

### “Can ordinary PCG legally use a noisy asymmetric preconditioner?”

Its standard convergence proof assumes a fixed SPD preconditioner, so not cleanly. It can still work empirically, as the paper demonstrates. I added a restart safeguard, but a proper study should compare flexible Krylov methods, especially FGMRES.

### “What is the next reproducible milestone?”

Implement the new paper’s exact `64×64` geometry, CSR `U V` operation, weighted Jacobi with `ω=0.9`, signed 3-bit coefficients, and residual replacement every five steps. Compare convergence against floating point and then substitute the same photonic MVM model into multigrid.

---

## 14. The honest status

### Completed

- Reconstructed the uploaded solver.
- Corrected its physical/dimensional description.
- Understood CG and PCG’s role in the old paper.
- Implemented a 2D Poisson example.
- Added quantization, noise, averaging, asymmetric smoothing, residual refinement, and MVM counters.
- Verified convergence and generated plots.
- Read and mapped the new coherent-MPU paper.
- Built a technical presentation.

### Not yet completed

- Calibration against measured photonic MVM data.
- Exact reproduction of the old paper’s capacitor geometry and published operation counts.
- Exact reproduction of Zhu et al.’s grounded-shell Poisson problem.
- Schrödinger/LOBPCG and LQCD cases.
- DAC/ADC, bandwidth, latency, and energy model.
- Experimental photonic hardware.

That is still good progress. The simulation has crossed the important boundary from “a digital solver inspired by photonics” to “a hybrid solver with an explicit replaceable photonic operator.”
