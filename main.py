import numpy as np
import pyamg
import scipy.sparse.linalg as spla

GRID = 64
TOL = 1e-10
NOISE = 0.045    # analog noise level, from the paper's Methods section
INNER = 5        # CG steps between residual-iteration restarts

rng = np.random.default_rng(0)

# 2D Poisson on a GRID x GRID mesh, u = 0 on the boundary:
#     4*u(i,j) - u(i-1,j) - u(i+1,j) - u(i,j-1) - u(i,j+1) = f(i,j)
A = pyamg.gallery.poisson((GRID, GRID), format="csr")

f = np.zeros((GRID, GRID))
f[GRID // 3, GRID // 4:3 * GRID // 4] = 2.0        # positive plate
f[2 * GRID // 3, GRID // 4:3 * GRID // 4] = -2.0   # negative plate
b = f.ravel()

N = A.shape[0]
count = {"float64": 0, "analog": 0}


def exact_mvm(v):
    count["float64"] += 1
    return A @ v


def noisy_mvm(v):
    count["analog"] += 1
    scale = np.abs(v).max()
    if scale == 0:
        return np.zeros_like(v)
    q = np.round(v / scale * 127) / 127               # 8-bit input
    y = A @ q / 4.0 + rng.normal(0, NOISE, v.shape)   # analog noise
    return y * 4.0 * scale


levels = pyamg.smoothed_aggregation_solver(A, max_levels=2, max_coarse=200).levels
P = levels[0].P          # coarse grid -> fine grid
R = levels[0].R          # fine grid -> coarse grid
A_coarse = levels[1].A.tocsr()

# OMEGA = 1 / (largest eigenvalue of A), found by power iteration
v = rng.standard_normal(N)
for _ in range(30):
    v = A @ v
    v /= np.linalg.norm(v)
OMEGA = 1.0 / abs(v @ (A @ v))


def smooth(rhs, mvm, sweeps):
    """Richardson iteration x <- x + OMEGA * (rhs - A x), starting from x = 0."""
    x = OMEGA * rhs                       # first step, since A @ 0 = 0
    for _ in range(sweeps - 1):
        x = x + OMEGA * (rhs - mvm(x))
    return x


def vcycle(r, mvm, pre, post):
    """Approximately solve A e = r, and return e."""
    e = smooth(r, mvm, pre)                               # remove rough error
    residual = r - exact_mvm(e)                           # what is left is smooth
    e = e + P @ spla.spsolve(A_coarse, R @ residual)      # fix it on the coarse grid
    if post:
        e = e + smooth(r - exact_mvm(e), mvm, post)       # tidy up after interpolating
    return e


def vcycle_exact(r):
    """The paper's digital setting: 2 sweeps before and 2 after."""
    return vcycle(r, exact_mvm, pre=2, post=2)


def vcycle_noisy(r):
    """The paper's hybrid setting: 4 sweeps before, none after."""
    return vcycle(r, noisy_mvm, pre=4, post=0)


# ---------------------------------------------------------------- the solvers
A_operator = spla.LinearOperator((N, N), matvec=exact_mvm, dtype=float)


def solve_plain():
    """Conjugate gradient with no preconditioner."""
    x, _ = spla.cg(A_operator, b, rtol=TOL, maxiter=2000)
    return x


def solve_preconditioned(preconditioner):
    """CG with a V-cycle preconditioner."""
    M = spla.LinearOperator((N, N), matvec=preconditioner, dtype=float)
    x, _ = spla.cg(A_operator, b, M=M, rtol=TOL, maxiter=2000)
    return x


def solve_with_restarts(preconditioner):
    """The same, restarted from an exactly recomputed residual (residual iteration)."""
    M = spla.LinearOperator((N, N), matvec=preconditioner, dtype=float)
    x = np.zeros(N)
    target = TOL * np.linalg.norm(b)
    for _ in range(100):
        r = b - exact_mvm(x)
        if np.linalg.norm(r) < target:
            break
        correction, _ = spla.cg(A_operator, r, M=M, rtol=1e-12, maxiter=INNER)
        x = x + correction
    return x


# ---------------------------------------------------------------- run and compare
def run(label, solver, *args):
    count["float64"] = 0
    count["analog"] = 0
    x = solver(*args)
    residual = np.linalg.norm(b - A @ x) / np.linalg.norm(b)
    print(f"{label:<28}{count['float64']:>9}{count['analog']:>8}{residual:>13.1e}")
    return count["float64"]


print(f"{GRID}x{GRID} Poisson, {N} unknowns\n")
print(f"{'solver':<28}{'float64':>9}{'analog':>8}{'||r||/||b||':>13}")

plain = run("plain CG", solve_plain)
digital = run("multigrid CG", solve_preconditioned, vcycle_exact)
hybrid = run("multigrid CG, photonic", solve_with_restarts, vcycle_noisy)

print(f"\nG = {plain / hybrid:.1f}   ({100 * (1 - hybrid / plain):.0f}% fewer float64 products)")