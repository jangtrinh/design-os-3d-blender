# Repeat Zones, Recursive Fractals & Iterative Solvers in Geometry Nodes

While Simulation Zones iterate across timeline animation frames ($t$), **Repeat Zones** (introduced in Blender 4.0) execute multi-pass iterative loops **within a single static frame evaluation**, enabling procedural fractals, L-System branching structures, and iterative relaxation solvers.

---

## 1. The Repeat Zone Architecture: Intra-Frame For-Loops

```
   [ Initial Mesh Input ]
             │
             ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                       REPEAT ZONE                           │
    │                                                             │
    │   [ Repeat Input ] ──► [ Procedural Transformation ]        │
    │         ▲                      │                            │
    │         │ (Pass to Next Iter)  ▼                            │
    │         └─────────────── [ Repeat Output ]                  │
    │                                │                            │
    │              Repeats N Times (Iteration Index i = 0..N-1)   │
    └────────────────────────────────┼────────────────────────────┘
                                     ▼
                      [ Fully Converged Output Mesh ]
```

### 1.1 Structural Properties
*   **Iteration Count ($N$):** Number of loop passes ($N \in [1, 1000]$).
*   **Iteration Index ($i$):** An integer field indicating the current zero-based loop cycle. Allows modulating parameters dynamically (e.g. scale factor $s = 0.5^i$, branch angle $\theta = 25^\circ \times i$).
*   *Memory Complexity:* Geometry is overwritten in place or appended; outputs pass directly to the next iteration without disk caching.

---

## 2. Lindenmayer Systems (L-Systems) & Procedural Branching

Aristid Lindenmayer (1968) introduced formal string rewriting grammars to describe plant morphogenesis:

```
        Iteration 0 (Trunk)          Iteration 1 (Primary Branches)      Iteration 2 (Twigs)
                 │                                \   /                           \ /   \ /
                 │                    ════►        \ /                 ════►       \     /
                 │                                  │                               │   │
```

### 2.1 The Grammar Rules in Geometry Nodes
*   **Axiom (Root):** A single vertical line segment of length $L_0$.
*   **Production Rule ($F \to F [+F] [-F]$):**
    On each loop pass $i$ in the Repeat Zone:
    1.  Take the endpoints of newly generated branches.
    2.  Spawn two child branches at bifurcated angles: $+\theta$ and $-\theta$ ($\approx 25^\circ\text{–}35^\circ$).
    3.  Scale child branch length by golden ratio decay: $L_{i+1} = L_i \times 0.707$.
    4.  Scale child branch radius by **Leonardo da Vinci's Rule of Trees**:
        $$r_{parent}^2 = r_{child1}^2 + r_{child2}^2 \implies r_{child} = \frac{r_{parent}}{\sqrt{2}} \approx 0.707 \cdot r_{parent}$$

### 2.2 Exponential Explosion Warning ($O(2^N)$)
A binary branching tree doubles in element count with every iteration:
$$N_{branches} = 2^0 + 2^1 + 2^2 + \dots + 2^M = 2^{M+1} - 1$$
*   At iteration $M = 10$: $2047\text{ branches}$ (Fast, realtime).
*   At iteration $M = 20$: $2,097,151\text{ branches}$ (Consumes several gigabytes of RAM; freezes Blender).
*   *Rule:* Keep recursive tree Repeat Zone iterations strictly bounded to **$N \le 8\text{–}12$**.

---

## 3. Iterative Mesh Relaxation & Laplacian Smoothing

In complex procedurally generated meshes or boolean unions, triangles can have poor aspect ratios (needle triangles) and uneven vertex spacing.

```
       Irregular Jagged Mesh                  After 10 Repeat Zone Laplacian Iterations
       ┌───/\─/\────/\───┐                    ┌───────────────────────┐
       │  /  \  \  /  \  │         ════►      │   Smooth Harmonic     │
       └───\/─\/────\/───┘                    │   Equilateral Quads   │
       Extreme local curvature!               └───────────────────────┘
```

### 3.1 The Discrete Laplacian Operator
At iteration $k+1$, shift each vertex toward the centroid of its 1-ring neighbor vertices:
$$\mathbf{p}_i^{(k+1)} = \mathbf{p}_i^{(k)} + \lambda \cdot \frac{1}{M_i} \sum_{j \in \mathcal{N}(i)} \left( \mathbf{p}_j^{(k)} - \mathbf{p}_i^{(k)} \right)$$
Where $\lambda \in (0, 1)$ is the relaxation step size.
*   **Geometry Nodes Implementation:**
    *   Inside the Repeat Zone, an `Offset Corner` or `Sample Index` node queries the average position of connected vertex neighbors.
    *   `Set Position` nudges vertices toward this average.
    *   Executing $N = 10\text{–}25\text{ iterations}$ produces smooth, organic surfaces and removes high-frequency CAD boolean artifacts.

---

## 4. References & Standards

1.  **Lindenmayer, A. (1968).** *Mathematical models for cellular interactions in development I. & II.* Journal of Theoretical Biology, 18(3), 280–315. (The foundational theory of L-Systems and branching automata).
2.  **Prusinkiewicz, P., & Lindenmayer, A. (1990).** *The Algorithmic Beauty of Plants.* Springer-Verlag, New York. (The classic text on algorithmic botanical modeling).
3.  **Mandelbrot, B. B. (1982).** *The Fractal Geometry of Nature.* W. H. Freeman and Company, New York. (Mathematical foundations of self-similarity and recursive geometry).
4.  **Sorkine, O. (2005).** *Laplacian Mesh Processing.* Eurographics 2005 STAR (State of The Art Report). (Discrete surface laplacians, umbrella operators, and iterative smoothing).
