# Simulation Zones & Numerical Physics Solvers in Geometry Nodes

Blender 3.6 introduced **Simulation Zones** (`Simulation Input` and `Simulation Output`), elevating Geometry Nodes from a static modifier into a **Turing-Complete, State-Persistent Physics Simulation Engine**.

---

## 1. The Simulation Loop Architecture & State Persistence

```
       [ Frame 0 / Initial Geometry State ]
                         │
                         ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                    SIMULATION ZONE                          │
        │                                                             │
        │   [ Simulation Input ] ──► [ Force & Collision Math ]       │
        │           ▲                            │                    │
        │           │ (Persistent State)         ▼                    │
        │           └───────────────── [ Simulation Output ]          │
        └─────────────────────────────────────────────────────────────┘
                         │
                         ▼
          Rendered Frame Output (Geometry Cache)
```

### 1.1 How State Persists Between Frames
*   Standard nodes evaluate strictly based on the current scene frame number ($t$).
*   Inside a **Simulation Zone**, values passed into `Simulation Output` at frame $t$ are fed directly back into `Simulation Input` at frame $t + 1$.
*   This allows numerical integration of time-dependent Ordinary Differential Equations (ODEs).

---

## 2. Numerical Integration: Euler vs. Symplectic Euler vs. Verlet

To update velocity $\mathbf{v}$ and position $\mathbf{x}$ under acceleration $\mathbf{a} = \frac{\mathbf{F}}{m}$ over time-step $\Delta t = \frac{1}{\text{FPS}}$:

```
        Explicit Forward Euler (Unstable)             Symplectic Euler (Volume Preserving)
        ┌───────────────────────────────┐             ┌───────────────────────────────┐
        │ Velocity updated from OLD pos;│             │ Velocity updated FIRST, then  │
        │ Energy blows up to infinity!  │             │ position updated from NEW vel.│
        │ Particles explode!            │             │ Stable orbital physics!       │
        └───────────────────────────────┘             └───────────────────────────────┘
```

### 2.1 Explicit Forward Euler (Divergent - Avoid in Geometry Nodes)
$$\mathbf{x}_{t+\Delta t} = \mathbf{x}_t + \mathbf{v}_t \Delta t$$
$$\mathbf{v}_{t+\Delta t} = \mathbf{v}_t + \frac{\mathbf{F}(\mathbf{x}_t)}{m} \Delta t$$
*Why It Fails:* In spring-mass systems or gravity orbits, explicit Euler injects false energy at every step; oscillating particles spiral outward and blow up.

### 2.2 Symplectic (Semi-Implicit) Euler (The Geometry Nodes Standard)
$$\mathbf{v}_{t+\Delta t} = \mathbf{v}_t + \frac{\mathbf{F}(\mathbf{x}_t)}{m} \Delta t$$
$$\mathbf{x}_{t+\Delta t} = \mathbf{x}_t + \mathbf{v}_{t+\Delta t} \Delta t$$
*Mathematical Superiority:* Symplectic Euler preserves phase space volume (Liouville's theorem). Orbits and pendulum swings remain stable indefinitely.

### 2.3 Velocity Verlet Integration (Molecular Dynamics)
$$\mathbf{x}_{t+\Delta t} = \mathbf{x}_t + \mathbf{v}_t \Delta t + \frac{1}{2} \mathbf{a}_t \Delta t^2$$
$$\mathbf{v}_{t+\Delta t} = \mathbf{v}_t + \frac{\mathbf{a}_t + \mathbf{a}_{t+\Delta t}}{2} \Delta t$$
Achieves second-order accuracy ($O(\Delta t^2)$) with minimal computational cost.

---

## 3. Craig Reynolds' Boids Flocking in Geometry Nodes

A classic multi-agent autonomous swarm requires evaluating three steering forces for every point $i$:

```
        Separation Force (Steer to avoid crowding local flockmates)
        ◄── • ──►
        
        Alignment Force (Steer towards the average heading of local flockmates)
        ════► • ════►
        
        Cohesion Force (Steer to move toward the average position of local flockmates)
        ──► • ◄──
```

### 3.1 Mathematical Steering Vectors
1.  **Separation ($\mathbf{F}_{sep}$):**
    $$\mathbf{F}_{sep} = \sum_{j \neq i, \|\mathbf{r}_{ij}\| < d_{sep}} \frac{\mathbf{x}_i - \mathbf{x}_j}{\|\mathbf{x}_i - \mathbf{x}_j\|^2}$$
2.  **Alignment ($\mathbf{F}_{align}$):**
    $$\mathbf{F}_{align} = \left( \frac{1}{N_{nbr}} \sum_{j=1}^{N_{nbr}} \mathbf{v}_j \right) - \mathbf{v}_i$$
3.  **Cohesion ($\mathbf{F}_{coh}$):**
    $$\mathbf{F}_{coh} = \left( \frac{1}{N_{nbr}} \sum_{j=1}^{N_{nbr}} \mathbf{x}_j \right) - \mathbf{x}_i$$
4.  **Blender Geometry Nodes Implementation:**
    *   Evaluated using `Sample Nearest Surface` or `Index of Nearest` nodes to query neighboring point indices within a search radius.
    *   Combined force $\mathbf{F}_{total} = w_s \mathbf{F}_{sep} + w_a \mathbf{F}_{align} + w_c \mathbf{F}_{coh}$ updates velocity in the Simulation Zone.

---

## 4. Sub-Stepping, Collisions & Bake Caching

*   **Sub-Stepping:** If high-speed particles pass through thin walls between frames (tunneling), the Simulation Zone must execute multiple iterations per frame.
    *   *Solution:* Place a **Repeat Zone** *inside* the Simulation Zone set to $N_{sub} = 4\text{–}10\text{ iterations}$, setting $\Delta t_{sub} = \frac{\Delta t}{N_{sub}}$.
*   **Bake Node (Blender 4.1+):**
    The `Bake` node caches simulation geometry directly to disk (OpenVDB / Alembic stream). This frees RAM and guarantees identical playback behavior across render farms and headless CLI batch tasks.

---

## 5. References & Standards

1.  **Verlet, L. (1967).** *Computer "Experiments" on Classical Fluids. I. Thermodynamical Properties of Lennard-Jones Molecules.* Physical Review, 159(1), 98–103. [DOI: 10.1103/PhysRev.159.98] (Foundational paper on time-reversible numerical integration).
2.  **Reynolds, C. W. (1987).** *Flocks, herds and schools: A distributed behavioral model.* ACM SIGGRAPH Computer Graphics, 21(4), 25–34. [DOI: 10.1145/37402.37406] (The boids algorithm for emergent swarm behaviors).
3.  **Müller, M., Heidelberger, B., Hennix, M., & Ratcliff, J. (2007).** *Position based dynamics.* Journal of Visual Communication and Image Representation, 18(2), 109–118. (Unconditionally stable constraint-based physics simulation).
4.  **Blender Foundation. (2024).** *Blender Documentation: Simulation Zones in Geometry Nodes.* https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/simulation/
