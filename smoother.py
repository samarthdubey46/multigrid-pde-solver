import numpy as np
import pyamg
import scipy.sparse as sp
import matplotlib.pyplot as plt

# Building matricesa
def scipy_sp(N):
    h = 1.0 / (N + 1)
    main = 2.0 * np.ones(N)
    off = -1.0 * np.ones(N - 1)
    A = sp.diags([off, main, off], offsets=[-1, 0, 1], format='csr')
    return A / h ** 2

def build_b(N,f,u_left,u_right):
    h = 1.0 / (N + 1)
    x = np.arange(1,N+1) * h
    b = f(x).astype(float)
    b[0] += u_left / h**2
    b[-1] += u_right / h**2
    return b
def build_omega(ml,levels,A):
    omega = np.zeros(levels)
    omega[0] = 1 / sp.linalg.eigsh(A, k=1, which='LM', return_eigenvectors=False)[0]
    for i in range(1,levels):
        omega[i] = 1/ sp.linalg.eigsh(ml.levels[i].A, k=1, which='LM', return_eigenvectors=False)[0]
    return omega
N = 16
max_coarse = 3
A = scipy_sp(N)
b = build_b(N, lambda x: np.ones_like(x), 100, 0)    # → [2501, 1, 1, 1]
ml = pyamg.smoothed_aggregation_solver(A, max_coarse=max_coarse)
n_levels = len(ml.levels)
omega = build_omega(ml,levels=n_levels,A=A)
A = []
for level in ml.levels:
    A.append(level.A)
# Smoothing
def smooth(l,x_,rhs,sweep):
    for _ in range(sweep):
        x_ += omega[l] * (rhs - A[l] @ x_)
    return x_

def plot(r_history):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.semilogy(range(len(r_history)), r_history, marker='o', color='#D85A30')
    ax.set_xlabel('outer iteration')
    ax.set_ylabel('‖r‖₂  (log scale)')
    ax.set_title('Residual history')
    ax.grid(True, which='both', alpha=0.3)
    plt.show()


def v_cycle(l,rhs,sweeps = 3):
    if l == len(ml.levels) - 1:  # coarsest: no P/R here
        return np.linalg.solve(A[l].toarray(), rhs)
    epsilon = np.zeros_like(rhs)
    epsilon = smooth(l,epsilon,rhs,sweeps)
    r = rhs - A[l] @ epsilon
    r_c = ml.levels[l].P.T @ r
    e_c = v_cycle(l+1,r_c,sweeps)
    epsilon += ml.levels[l].P @ e_c
    epsilon = smooth(l,epsilon,rhs,sweeps)
    return epsilon

def pcg(rhs,x_0,max_iter,tol=1e-8):
    x = x_0.copy()
    r = rhs - A[0] @ x
    z = v_cycle(0,r)
    p = z
    rz = r @ z
    for k in range(max_iter):
        Ap = A[0] @ p
        alpha = rz / (p@Ap)
        x += alpha*p
        r = r - alpha*Ap
        if np.linalg.norm(r) < tol * np.linalg.norm(rhs):
            break
        z = v_cycle(0,r)
        rz_new = r @ z
        B = rz_new / rz
        p = z + B*p
        rz = rz_new
    return x,k

def solve(rhs, tol=1e-12, max_outer=10, pcg_maxiter=20, pcg_tol=1e-2):
    x = np.zeros_like(rhs)
    r_history = []
    for outer in range(max_outer):
        r = rhs - A[0] @ x
        r_history.append(np.linalg.norm(r))
        if r_history[-1] < tol * np.linalg.norm(rhs):
            break
        delta,steps = pcg(r, np.zeros_like(r), pcg_maxiter, tol=pcg_tol)
        print(steps)
        x = x + delta

    return x, r_history

x,r_hist = solve(b)
print(np.array(A))
print(x)
plot(r_hist)

r = b - A @ x
