I’ll anchor the explanation to your `smoother.py`, then connect PCG to gradient descent and point you to a short study path with reliable references.

Your file actually has two nested iterative ideas: a multigrid V-cycle is used as the preconditioner, and PCG uses that preconditioner to choose better search directions. I’m checking a few canonical references so the reading order is useful, not just a pile of links.

PCG means **Preconditioned Conjugate Gradient**. Since you understand gradient descent, the easiest route is:

> Gradient descent → conjugate gradient (CG) → preconditioning → PCG.

## 1. Solving a linear system as optimization

Your program solves

\[
Ax=b,
\]

where \(A\) is the finite-difference matrix for the 1D Poisson equation. This matrix is symmetric positive definite (SPD), which is exactly what CG requires.

Solving \(Ax=b\) is equivalent to minimizing

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

is the residual.

Therefore, the residual is the negative gradient.

## 2. From gradient descent to CG

Gradient descent moves in the negative-gradient direction:

\[
x_{k+1}=x_k+\alpha_k r_k.
\]

On a quadratic, an exact line search gives

\[
\alpha_k=\frac{r_k^Tr_k}{r_k^TAr_k}.
\]

The problem is that successive gradient directions may partly undo earlier progress. On a long, narrow quadratic bowl, gradient descent zigzags.

CG instead uses

\[
p_k=r_k+\beta_kp_{k-1}.
\]

The new direction combines:

- the current negative gradient \(r_k\);
- memory of the preceding direction \(p_{k-1}\).

The value of \(\beta_k\) is selected so that the search directions are **\(A\)-conjugate**:

\[
p_i^TAp_j=0,\qquad i\ne j.
\]

Geometrically, CG chooses directions that do not undo minimization already performed along previous directions.

A basic CG iteration is:

\[
\begin{aligned}
\alpha_k &=
\frac{r_k^Tr_k}{p_k^TAp_k},\\
x_{k+1} &= x_k+\alpha_kp_k,\\
r_{k+1} &= r_k-\alpha_kAp_k,\\
\beta_k &=
\frac{r_{k+1}^Tr_{k+1}}{r_k^Tr_k},\\
p_{k+1} &= r_{k+1}+\beta_kp_k.
\end{aligned}
\]

In exact arithmetic, CG solves an \(n\times n\) SPD system in at most \(n\) iterations. Its practical speed depends mainly on the eigenvalue distribution and condition number of \(A\).

## 3. Why preconditioning is needed

The Poisson matrix becomes increasingly ill-conditioned as the grid is refined. In the optimization picture, the quadratic bowl becomes very stretched.

A preconditioner \(M\) approximates \(A\), but is much cheaper to solve with:

\[
M\approx A.
\]

Instead of using \(r\) directly, PCG computes

\[
Mz=r,
\]

or equivalently

\[
z=M^{-1}r.
\]

Because \(M^{-1}\) approximates \(A^{-1}\),

\[
z\approx A^{-1}r.
\]

But \(A^{-1}r\) is exactly the correction that would remove the current error. Thus:

- \(r\): tells you how wrong the current solution is;
- \(M^{-1}r\): estimates how the solution should be corrected.

PCG uses

\[
p_k=z_k+\beta_kp_{k-1}
\]

and

\[
\begin{aligned}
\alpha_k &= \frac{r_k^Tz_k}{p_k^TAp_k},\\
\beta_k &= \frac{r_{k+1}^Tz_{k+1}}{r_k^Tz_k}.
\end{aligned}
\]

A good preconditioner makes the eigenvalues of the transformed operator

\[
M^{-1/2}AM^{-1/2}
\]

cluster near \(1\). PCG then converges in many fewer iterations.

## 4. PCG in your code

The PCG implementation starts at [smoother.py:65](/home/samarth/dev/multigrid-pde-solver/smoother.py:65).

### Initial residual

```python
r = rhs - A[0] @ x
```

This computes

\[
r_0=b-Ax_0=-\nabla\phi(x_0).
\]

### Apply the multigrid preconditioner

```python
z = v_cycle(0, r)
```

Conceptually, this is

\[
z=M^{-1}r.
\]

There is no explicit matrix called \(M\). The operation “apply \(M^{-1}\)” is implemented by one multigrid V-cycle.

The V-cycle approximately solves

\[
Az=r.
\]

If it solved this exactly, then \(z=A^{-1}r\) would be the exact error correction.

### First search direction

```python
p = z
rz = r @ z
```

Thus \(p_0=z_0\), the preconditioned negative-gradient direction.

### Exact minimization along \(p\)

```python
Ap = A[0] @ p
alpha = rz / (p @ Ap)
x += alpha * p
r = r - alpha * Ap
```

This performs

\[
x_{k+1}=x_k+\alpha_kp_k
\]

with

\[
\alpha_k=\frac{r_k^Tz_k}{p_k^TAp_k}.
\]

The residual update avoids recomputing \(b-Ax\) from scratch.

### Construct the next conjugate direction

```python
z = v_cycle(0, r)
rz_new = r @ z
B = rz_new / rz
p = z + B * p
```

This corresponds to

\[
\beta_k=\frac{r_{k+1}^Tz_{k+1}}{r_k^Tz_k},
\qquad
p_{k+1}=z_{k+1}+\beta_kp_k.
\]

`B` would conventionally be named `beta`.

## 5. Why multigrid is a good preconditioner

Your V-cycle is at [smoother.py:53](/home/samarth/dev/multigrid-pde-solver/smoother.py:53).

It works because different mechanisms remove different error components:

1. Richardson smoothing removes rapidly oscillating, high-frequency error.
2. Restriction transfers the remaining residual to a coarse grid.
3. On the coarse grid, smooth error looks more oscillatory and is easier to eliminate.
4. Prolongation transfers the coarse correction back.
5. Post-smoothing removes errors introduced during interpolation.

So the relationship is:

\[
\boxed{\text{PCG decides how to combine corrections}}
\]

while

\[
\boxed{\text{multigrid cheaply produces each approximate correction}}.
\]

## 6. One unusual aspect of your program

Your outer `solve()` loop calls PCG on the current residual:

```python
delta, steps = pcg(r, np.zeros_like(r), ...)
x = x + delta
```

Therefore, each call approximately solves

\[
A\delta=r,
\]

then applies \(x\leftarrow x+\delta\).

This is an outer iterative-correction scheme containing short, restarted PCG solves. It can work, but standard PCG would usually be called once:

```python
x, steps = pcg(b, np.zeros_like(b), max_iter, tol=1e-12)
```

Restarting PCG discards its accumulated conjugate directions, potentially slowing convergence. Also, `k` is a zero-based loop index, so the returned iteration count is one smaller than the number of iterations actually performed.

## Recommended study order

1. **Jonathan Shewchuk — “An Introduction to the Conjugate Gradient Method Without the Agonizing Pain.”**  
   Start here. It develops CG from the quadratic-bowl picture and explains conditioning and preconditioning intuitively.

2. **Netlib — Templates for the Solution of Linear Systems**, especially sections 2.3.1 and 3.  
   This gives the standard PCG algorithm and practical preconditioner discussion: [Netlib PDF](https://www.netlib.org/templates/templates.pdf).

3. **Stanford EE364B, Lecture 13 — CG recap.**  
   Useful once the connection with quadratic minimization is comfortable: [Stanford lecture](https://see.stanford.edu/Course/EE364B/105).

4. **SciPy’s CG documentation.**  
   Use this to compare your implementation against a production interface: [SciPy `cg`](https://scipy.github.io/devdocs/reference/generated/scipy.sparse.linalg.cg.html).

For your immediate learning, I would study in this order:

\[
\text{quadratic minimization}
\rightarrow
\text{exact line search}
\rightarrow
A\text{-conjugate directions}
\rightarrow
\text{CG algorithm}
\rightarrow
\text{condition numbers}
\rightarrow
\text{PCG}
\rightarrow
\text{multigrid preconditioning}.
\]