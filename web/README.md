# Photonic PDE Lab

Open `index.html` directly in a browser. No build, server, network, or runtime dependencies. **Download HTML** inside **Explore details** saves a fresh, self-contained copy.

The guided bench starts paused. **Next** advances one solver event; **Play/Pause** controls both presentation time and solver advancement. **Restart** cancels pending animation and retains the selected starting guess. Components and overview stages reveal explanations without changing the solve. Reduced-motion mode uses static highlights.

The original sparse matrix data, numerical engine, tolerances, iteration limits, counters, `PhotonicSolver`, existing `PhotonicLab` methods, and three registered tool definitions are preserved. Presentation state is separate; `PhotonicLab.next()` and `playPause()` expose the new controls. The 64-point problem retains boundary values 100 and 0. The simulation models ideal multiplication, not optical timing, signed brightness, or hardware noise.

## Verification

Numerical checks use only Node:

```sh
node web/verify.cjs --core-only
```

Full browser checks require Playwright and its Chromium browser (or `CHROME_PATH` pointing to an installed Chrome):

```sh
node web/verify.cjs
```

The suite checks all three starting guesses, exact within-browser equivalence of manual Next / autoplay / finish, real pause/resume timing, repeated clicks, restart, changing levels, CPU-only work, terminal states, keyboard focus, reduced motion, offline download, and overflow with every details panel expanded at 320–1440px. Autoplay equivalence uses a deterministic animation clock; pause/resume uses real browser time. Error and iteration-limit presentation use fault injection, without modifying production solver settings. Cross-runtime numerical comparisons allow last-bit floating-point differences.

| Starting guess | Relative residual | Optical / digital MVMs |
| --- | --- | --- |
| Zero | 3.1704 × 10⁻¹³ | 180 / 111 |
| Linear | 1.0770 × 10⁻¹³ | 126 / 77 |
| Random | 1.5004 × 10⁻¹⁴ | 198 / 123 |

Actual browser screenshots and the check report are in [validation](validation/). Both desktop and mobile include ready, optical multiply, CPU update, details, and completed states. The test harness is optional; distributing `index.html` alone is sufficient.

## Hardware mapping — shared feedback loop

The bench uses one shared encoder/DAC and detector/ADC, with three separately visible fixed optical matrix blocks A₀/A₁/A₂. Only the selected level receives an optical smoothing request. CPU-only work leaves optical traffic idle; the CPU may perform several operations before issuing another request. A₃ remains a CPU direct solve. Routing lines describe functional level selection; physical switching technology and optical channel encoding are unspecified. This is the selected presentation architecture, not a validated physical hardware implementation.

## Full-screen guided workspace

The Full screen control expands the main workspace: CPU control flow, hardware feedback loop, and live vector/solution panel. On narrow screens these panels stack. The CPU flow highlights the current outer stage and reveals the active PCG or multigrid routine, with the current operation, purpose, and equation.

The vector panel distinguishes the full 64-value solution `x` from the local multigrid estimate `eℓ` and detected product `yℓ = Aℓeℓ`. It shows actual event values, including the CPU's before/after smoothing update, and explains when `x` remains unchanged while its correction is computed. All 64 values of `x` are available in a disclosure. A zero input is explicitly identified; beam animation indicates a transfer, not numerical magnitude. The matrix selector lists the fixed A, R, and P operators and their roles.

Browser verification includes entering/exiting full screen, initial `x` values, and the CPU update's live vectors. Numerical baselines and manual/autoplay/finish equivalence remain unchanged.

## Continuous flowchart

Open [loop.html](loop.html) for one connected map of the complete browser solve. It embeds an unchanged copy of the existing sparse data and solver engine, so this file works offline on its own. CPU correction and PCG paths connect to the recursive multigrid path and its shared encoder → selected A₀/A₁/A₂ → detector feedback loop. The three optical boxes are alternatives; vectors never traverse them in series. The 3×3 coarse solve, restriction, prolongation and PCG remain digital.

Play follows actual solver events; Next advances one operation. During animation, another Next completes the current transfer. Pause freezes solver and transfer progress; Restart cancels the pending frame. Follow active step scrolls the map as control moves; disable it to inspect the whole map. Click operations for explanations or Matrices for all ten fixed operators. The exact solution is a reference diagnostic and never enters the algorithm.

This page depicts the 64-unknown ideal browser configuration, not the 4096-unknown noisy experiment in `main.py`. Numerical checks and desktop/mobile screenshots: `node web/verify-loop.cjs` (requires Playwright and Chrome). Council record: [loop-council.md](loop-council.md).
