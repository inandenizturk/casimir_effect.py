# 2D Dynamical Casimir Effect (DCE) Simulation via FDTD

A high-performance numerical simulation of the **Dynamical Casimir Effect (DCE)** using a 2D Finite-Difference Time-Domain (FDTD) scalar wave solver in Python.

The project models particle creation from the quantum vacuum induced by a relativistic, oscillating conducting boundary (mirror) via parametric resonance. Output frames are rendered via custom vectorized transfer functions and streamed directly into an FFmpeg pipe to bypass disk I/O bottlenecks.

---

## Mathematical Derivations & Numerical Methods

### 1. The Continuous Wave Equation
The scalar field $\psi(x, y, t)$ obeys the 2D homogeneous wave equation ($c = 1$):

$$\frac{\partial^2 \psi}{\partial t^2} = \nabla^2 \psi = \frac{\partial^2 \psi}{\partial x^2} + \frac{\partial^2 \psi}{\partial y^2}$$

### 2. Temporal Discretization (Central Differences)
Expanding $\psi(t)$ into Taylor series around time step $t^n = n\Delta t$:

$$\psi^{n+1} = \psi^n + \Delta t \left.\frac{\partial \psi}{\partial t}\right|^n + \frac{\Delta t^2}{2} \left.\frac{\partial^2 \psi}{\partial t^2}\right|^n + \mathcal{O}(\Delta t^3)$$

$$\psi^{n-1} = \psi^n - \Delta t \left.\frac{\partial \psi}{\partial t}\right|^n + \frac{\Delta t^2}{2} \left.\frac{\partial^2 \psi}{\partial t^2}\right|^n - \mathcal{O}(\Delta t^3)$$

Summing both expansions eliminates odd-order derivatives:

$$\psi^{n+1} + \psi^{n-1} = 2\psi^n + \Delta t^2 \left.\frac{\partial^2 \psi}{\partial t^2}\right|^n + \mathcal{O}(\Delta t^4)$$

Solving for the second-order temporal derivative yields:

$$\left.\frac{\partial^2 \psi}{\partial t^2}\right|^n = \frac{\psi^{n+1} - 2\psi^n + \psi^{n-1}}{\Delta t^2} + \mathcal{O}(\Delta t^2)$$

### 3. Spatial Laplacian (5-Point Stencil)
On a uniform spatial grid with $\Delta x = \Delta y = 1.0$:

$$\left(\nabla^2 \psi\right)_{i,j}^n \approx \frac{\psi_{i+1, j}^n + \psi_{i-1, j}^n + \psi_{i, j+1}^n + \psi_{i, j-1}^n - 4\psi_{i, j}^n}{\Delta x^2}$$

### 4. Leapfrog Update Scheme
Substituting the discrete derivatives into the governing equation:

$$\frac{\psi_{i,j}^{n+1} - 2\psi_{i,j}^n + \psi_{i,j}^{n-1}}{\Delta t^2} = c^2 \left(\nabla^2 \psi\right)_{i,j}^n$$

Solving explicitly for the future field $\psi_{i,j}^{n+1}$:

$$\psi_{i,j}^{n+1} = 2\psi_{i,j}^n - \psi_{i,j}^{n-1} + (c \Delta t)^2 \left(\nabla^2 \psi\right)_{i,j}^n$$

### 5. Numerical Stability (CFL Criterion)
In two dimensions, stability requires:

$$S = c \Delta t \sqrt{\frac{1}{\Delta x^2} + \frac{1}{\Delta y^2}} \le 1 \implies \Delta t \le \frac{\Delta x}{c\sqrt{2}} \approx 0.7071$$

With $\Delta t = 0.05$ and $\Delta x = 1.0$, the Courant number is $S \approx 0.0707 \ll 1$, ensuring strong numerical stability.

### 6. Dynamical Boundary & Parametric Resonance
The conducting boundary oscillates harmonically:

$$x_m(t) = x_0 + A \sin(\omega_m t)$$

* Equilibrium: $x_0 = \lfloor NX / 4 \rfloor$
* Amplitude: $A = 6.0$
* Angular frequency: $\omega_m = 2.4$

Parametric amplification occurs when the boundary oscillation frequency satisfies the condition $\omega_m \approx 2\omega_k$ for a cavity mode $k$. A homogeneous Dirichlet boundary condition is enforced across a 5-pixel slab:

$$\psi(x, y, t) = 0, \quad \forall x \in [\lfloor x_m(t) \rfloor - 2, \, \lfloor x_m(t) \rfloor + 2]$$

### 7. Analytical Color Transfer Function
Local normalized energy density is defined via field amplitude:

$$E_{i,j} = \text{clip}\left(8.0 \cdot |\psi_{i,j}|, \, 0.0, \, 1.0\right)$$

The color channels are mapped to 8-bit unsigned integers ($\mathbb{R} \to [0, 255] \cap \mathbb{Z}$):

$$R_{i,j} = \left\lfloor 180 \cdot E_{i,j}^{1.5} \right\rfloor$$

$$G_{i,j} = \left\lfloor 220 \cdot E_{i,j} \right\rfloor$$

$$B_{i,j} = \left\lfloor 255 \cdot \sqrt{E_{i,j}} \right\rfloor$$

---

## Architectural Highlights

* **Zero-I/O Video Pipeline:** Eliminates disk bottlenecks by piping raw contiguous `uint8` NumPy buffers directly into FFmpeg's `stdin` via `subprocess.Popen`.
* **Pure Mathematical Colormap:** Avoids external rendering engines (e.g., Matplotlib) by applying custom vector operations directly on image matrices.

---

## Prerequisites

* Python 3.9+
* NumPy
* FFmpeg (accessible in system `$PATH`)

```bash
# macOS (Homebrew)
brew install ffmpeg

# Ubuntu / Debian
sudo apt-get install ffmpeg
