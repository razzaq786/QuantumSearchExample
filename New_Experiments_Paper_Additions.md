# New Experiments — Strengthening the Contribution

Two new, real, reproducible experiments (code + data in the replication package). Both
were run as exact state-vector / wall-clock measurements — nothing here is projected or
hypothetical. Full methodology and honest scope limits are stated below; please read the
"What this does NOT establish" box before writing it into the abstract.

---

## Experiment A — Gate-level reversible multi-condition oracle

**What changed:** the oracle is no longer a classical C# callback. It is a genuine
reversible circuit built from H, X, and multi-controlled-X (MCX) gate primitives,
operating on a quantum-encoded index register plus explicit ancilla qubits, with a
standard phase-kickback flag ancilla (the same construction pattern as your existing
Figure 3, generalised to k conditions). It was validated by exact state-vector
simulation (not an approximation) — every amplitude was tracked exactly through every
gate.

**Design:** N = 256 (n = 8 index qubits) was held **fixed** across all runs; only the
number of conjunctive conditions k varied (k = 1, 2, 4, 8), partitioning the same 8
index bits into k roughly-equal fields. This isolates oracle construction cost from
search-space-size effects — precisely the question EC1 was trying to answer. 30 trials
per k, random target pattern each trial, matching your existing 30-trial protocol.

**Results (measured, not projected):**

| k | ancilla qubits | total qubits | oracle calls | single-oracle gates | single-oracle depth | full-circuit gates | full-circuit depth | mean success prob. | empirical success (30 trials) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 | 10 | 12 | 35 | 6 | 850 | 157 | 0.9999 | 100% |
| 2 | 3 | 11 | 12 | 37 | 6 | 874 | 157 | 0.9999 | 100% |
| 4 | 5 | 13 | 12 | 41 | 6 | 922 | 157 | 0.9999 | 100% |
| 8 | 9 | 17 | 12 | 49 | 6 | 1018 | 157 | 0.9999 | 100% |

**Three genuine findings, one confirming EC1 and two refining it:**
1. **Ancilla count grows exactly linearly**, k+1 — confirms EC1 as stated.
2. **Gate count grows roughly linearly in k** (~2 additional gates per condition in
   this construction) — confirms EC1's spirit, with a measured constant now available
   instead of an assumed one.
3. **Circuit depth for a single oracle call is constant across k (always 6)** — this
   *refines* EC1's "depth grows as O(k)" claim. Because each condition's sub-circuit
   acts on a disjoint subset of qubits, they schedule in parallel; only the final
   k-controlled combine gate serializes on k. This is a real, non-obvious engineering
   result worth reporting as a refinement, not silently folded into "confirmed."

**What this does NOT establish** (be explicit about this in the paper, or a referee
will assume you're overclaiming again):
- N = 256 is far below the NFR1 target of 10^6; this validates the *construction
  pattern*, not production-scale feasibility.
- MCX gates are treated as native primitives (consistent with Q#'s `Controlled X`
  functor, which the QDK compiler decomposes automatically) — real hardware would
  transpile these into 1- and 2-qubit native gates, adding depth not modeled here,
  especially for the wider MCX gates (e.g., MCX8 at k=1).
- This is a noiseless, exact simulation (same limitation as your existing L1) — no
  decoherence or gate-fidelity error is modeled.
- The oracle marks a value based on the index register's own bit-pattern, not on
  externally quantum-encoded patient attribute data — QRAM-based data loading (EC3)
  remains unimplemented, as before.

---

## Experiment B — Real indexed classical baseline

**What changed:** an actual measured comparison of linear scan vs. hash-table lookup
vs. binary search, same machine, same 30-trial protocol, N up to 1,048,576 (matching
NFR1's target for the first time in this paper).

**Results (measured, milliseconds, mean of 30 trials):**

| N | linear scan | hash lookup | binary search | Grover oracle calls (theoretical) |
|---|---|---|---|---|
| 64 | 0.00089 | 0.000140 | 0.000596 | 6 |
| 1,024 | 0.01377 | 0.000127 | 0.000354 | 25 |
| 16,384 | 0.29106 | 0.000333 | 0.000679 | 100 |
| 65,536 | 1.08012 | 0.001102 | 0.001696 | 201 |
| 262,144 | 4.00775 | 0.003611 | 0.003345 | 402 |
| 1,048,576 | 18.76952 | 0.005060 | 0.007744 | 804 |

**Honest interpretation:** at N = 10^6, hash lookup is ~3,700x faster than linear
scan, and binary search ~2,400x faster — both dramatically faster than Grover's ~804
oracle calls could ever be for equality search, once any real oracle-invocation cost
is included. This *confirms* the paper's own honest caveat (L7): quantum search offers
no advantage over indexed retrieval for single-field equality lookup. Framed correctly,
this strengthens rather than weakens the paper — it shows you've precisely
characterized *where* the technique doesn't help, which is exactly what referees said
was missing, and sets up the real motivating case (composite, ad-hoc conjunctive
queries across attributes that aren't jointly indexed) as the place quantum search is
actually being proposed for.

**Bonus consistency check:** the hash-lookup times measured here (≈0.1–5 µs across
this N range) are the same order of magnitude as the illustrative $C_{eval} = 1\mu s$
assumed in Section 4.11 — you can now cite this as empirical support for that
assumption rather than leaving it as a bare hypothetical.

---

## Where to add this in the paper (ready-to-paste LaTeX)

### 1. Abstract — add after the multi-condition-oracle disclaimer sentence

```latex
A gate-level reversible oracle for up to eight conjunctive conditions was additionally
implemented and validated by exact state-vector simulation at fixed N=256, confirming
correct Grover amplification (>99.9% success probability, 100% empirical success
across 30 trials per condition count) and providing measured (not projected) ancilla,
gate-count, and circuit-depth scaling with the number of conditions k. A real indexed
classical baseline (hash lookup, binary search) was also measured against the
unindexed linear-scan baseline at N up to 10^6, confirming that indexed retrieval
dominates both classical and quantum unstructured search for single-field equality
lookup.
```

### 2. New subsection — insert after Section 4.16.2 as "4.16.3"

```latex
\subsection{Gate-Level Validation of the Multi-Condition Oracle (Small Scale)}
\label{sec:multicondition-validation}

To move the multi-condition oracle (Section 4.16.2) from a design-level specification
toward an implemented and empirically validated artefact, we built a gate-level
reversible oracle using H, X, and multi-controlled-X (MCX) primitives, following the
same phase-kickback ancilla pattern as the single-condition circuit in Figure 3,
generalised to $k$ conjunctive conditions over disjoint fields of a shared index
register. The oracle was validated by exact state-vector simulation (implemented
independently of the Q\#/Azure prototype, in Python/NumPy, to allow full control over
qubit count and enable exact amplitude tracking).

Dataset size was held fixed at $N=256$ ($n=8$ index qubits) across all configurations,
so that only the number of conditions $k$ varied -- isolating oracle construction cost
from search-space-size effects, which is the question EC1 (Section 4.5.4) originally
posed. $k \in \{1,2,4,8\}$ conditions were tested, each over a near-equal partition of
the 8 index bits, with 30 trials per $k$ (random target pattern per trial, matching the
protocol of Section 4.4.4).

Table~\ref{tab:oracle-scaling} reports the measured results.

\begin{table}[h]
\centering
\caption{Measured resource scaling of the gate-level multi-condition oracle, $N=256$ fixed, 30 trials per $k$.}
\label{tab:oracle-scaling}
\begin{tabular}{ccccccccc}
\toprule
$k$ & Ancilla & Total & Oracle & Single-oracle & Single-oracle & Full-circuit & Full-circuit & Success \\
 & qubits & qubits & calls & gate count & depth & gate count & depth & rate \\
\midrule
1 & 2 & 10 & 12 & 35 & 6 & 850 & 157 & 100\% \\
2 & 3 & 11 & 12 & 37 & 6 & 874 & 157 & 100\% \\
4 & 5 & 13 & 12 & 41 & 6 & 922 & 157 & 100\% \\
8 & 9 & 17 & 12 & 49 & 6 & 1018 & 157 & 100\% \\
\bottomrule
\end{tabular}
\end{table}

Three findings emerge. First, ancilla qubit count grows exactly as $k+1$, confirming
EC1's ancilla projection empirically. Second, gate count grows approximately linearly
in $k$ (a measured slope of $\approx 2$ additional gates per condition in this
construction), consistent with EC1's expectation. Third, and refining EC1's original
"depth grows as $O(k)$" projection: single-oracle-call \emph{circuit depth remained
constant at 6} across all tested $k$. This is because each condition's sub-circuit
acts on a disjoint subset of index qubits and its own dedicated ancilla, allowing
independent conditions to be scheduled in parallel; only the final $k$-controlled
combine gate serialises on $k$, and its contribution to depth did not dominate at the
tested scale. We report this as a refinement rather than a simple confirmation of EC1:
gate \emph{count} (and hence total execution time on hardware without free qubit
parallelism) grows with $k$ as expected, but circuit \emph{depth} need not, given
sufficient ancilla parallelism.

All 120 trials (4 values of $k$ $\times$ 30 trials) returned a measured index matching
the marked target, and mean success probability exceeded 0.999 in every configuration
-- confirming that the reversible construction correctly implements Grover
amplification at gate level, not merely at the abstraction level of the classical
callback used in Section 4.2.

\textbf{Scope.} This result validates the multi-condition \emph{oracle construction
pattern}, not production-scale feasibility: $N=256$ remains four orders of magnitude
below the NFR1 target of $10^6$, MCX gates are treated as native primitives (as Q\#'s
\texttt{Controlled} functor does, with hardware transpilation handled by the QDK
compiler) rather than decomposed to a hardware-native gate set, and no decoherence or
gate-fidelity noise is modeled (consistent with limitation L1). Extending this
validation to larger $N$, more conditions, and a noise model is scoped as future work
(FW1, FW3). Full simulation code and raw results are included in the replication
package.
```

### 3. Section 4.5.4 (EC1) — replace with the measured version

```latex
% OLD
EC1- Reversible circuit depth (projected, not implemented): Composing a
multi-condition oracle from Toffoli gates is expected to require circuit depth and
ancilla count that both grow at least linearly in the number of conditions k; this is
an analytical expectation drawn from standard reversible-circuit construction, not a
measured or gate-synthesized result in this study.

% NEW
EC1 - Reversible circuit resource scaling (now measured at small scale, Section
4.16.3): ancilla qubit count grows exactly as k+1 and gate count grows approximately
linearly in the number of conditions k, both empirically confirmed by gate-level
state-vector simulation at N=256 for k up to 8. Circuit depth for a single oracle
call, however, remained constant across k in this construction, because
condition-specific sub-circuits act on disjoint qubits and schedule in parallel; only
the final k-controlled combine step serialises on k. Extending this validation beyond
N=256 and modeling hardware-native gate decomposition remains future work (FW1, FW3).
```

### 4. Section 4.4 — new indexed-baseline subsection (after the existing scoping paragraph)

```latex
\subsubsection{Indexed Classical Baseline (Empirical)}
To move the baseline discussion above from caveat to measurement, we additionally
implemented and timed a hash-table lookup and a binary search over a sorted array,
alongside the linear scan, on the same machine, using the same 30-trial protocol,
across $N \in \{64, ..., 1{,}048{,}576\}$ -- for the first time in this paper reaching
the NFR1 target scale. Table~\ref{tab:indexed-baseline} reports the results.

\begin{table}[h]
\centering
\caption{Measured lookup time (ms, mean of 30 trials) by method and dataset size.}
\label{tab:indexed-baseline}
\begin{tabular}{ccccc}
\toprule
$N$ & Linear scan & Hash lookup & Binary search & Grover oracle calls (theoretical) \\
\midrule
64 & 0.00089 & 0.000140 & 0.000596 & 6 \\
1,024 & 0.01377 & 0.000127 & 0.000354 & 25 \\
16,384 & 0.29106 & 0.000333 & 0.000679 & 100 \\
65,536 & 1.08012 & 0.001102 & 0.001696 & 201 \\
262,144 & 4.00775 & 0.003611 & 0.003345 & 402 \\
1,048,576 & 18.76952 & 0.005060 & 0.007744 & 804 \\
\bottomrule
\end{tabular}
\end{table}

At $N=10^6$, hash lookup is approximately $3{,}700\times$ faster than linear scan and
binary search approximately $2{,}400\times$ faster; both are dramatically faster than
Grover's 804 theoretical oracle calls could deliver once any realistic per-oracle
invocation cost is included. This confirms empirically what Section 4.4's scoping
paragraph states analytically: quantum search offers no advantage over indexed
retrieval for single-field equality lookup, and the baseline in this study should be
read as isolating Grover's behaviour under the unstructured-search conditions it
targets, not as a claim of advantage over production database indexing. It also
motivates the real target for this line of work: composite, ad-hoc conjunctive
queries across attribute combinations that are not jointly covered by a single index
-- the multi-condition case examined analytically in Section 4.14 and validated at
small scale in Section 4.16.3.
```

### 5. Section 4.11 — add a grounding footnote to the illustrative example

```latex
% ADD after the Ceval assumption sentence:
This assumption is consistent with the hash-lookup times measured empirically in
Section 4.4 (Table~\ref{tab:indexed-baseline}), which range from approximately 0.1 to
5 $\mu$s across $N=64$ to $N=10^6$.
```

### 6. Abstract / Limitations — revise L2

```latex
% OLD
L2 - Single-condition oracle only: The implemented and validated oracle supports only
single-field patient-ID matching. Multi-condition conjunctive oracles are designed and
formalized but not yet implemented and empirically validated. The claim of O(n^{k/2})
complexity reduction for multi-condition queries therefore remains a theoretically
grounded projection rather than an experimentally confirmed result.

% NEW
L2 - Multi-condition validation is small-scale and gate-level only: A reversible,
gate-level multi-condition oracle (up to k=8 conditions) was implemented and validated
by exact state-vector simulation at N=256 (Section 4.16.3), confirming correct Grover
amplification and providing measured (not projected) resource scaling. This is
distinct from, and does not replace, the Azure/Q#/SQL Server production-style
prototype (Section 4.2), which remains single-condition only; nor does it validate
performance at the NFR1 target scale of N=10^6, hardware-native gate decomposition, or
noise robustness. The claim of O(n^{k/2}) complexity reduction for large-N
multi-condition queries therefore remains a theoretically grounded projection,
supported by, but not equivalent to, the small-scale gate-level result.
```

### 7. Contributions (C2) — broaden to reflect the new validated scope

```latex
% OLD
C2 - Prototype: A working prototype, implemented in Azure Functions, Q#, and SQL
Server, demonstrating end-to-end interoperability of classical orchestration and
quantum search execution; accompanied by a publicly available replication package.

% NEW
C2 - Prototype: A working single-condition prototype implemented in Azure Functions,
Q#, and SQL Server, demonstrating end-to-end interoperability of classical
orchestration and quantum search execution; together with an independently validated,
gate-level reversible multi-condition oracle (Section 4.16.3, k up to 8, small scale),
moving the multi-condition design from specification toward empirical validation.
Accompanied by a publicly available replication package including both codebases.
```

### 8. Conclusion — update RQ3 answer and Contributions summary

```latex
% OLD (Conclusion, RQ3 sentence)
RQ3 identified three principal engineering constraints for oracle extension: O(k)
reversible circuit depth growth, ETL denormalisation fidelity requirements, and QRAM
dependency for datasets exceeding N > 10^6.

% NEW
RQ3 identified three principal engineering constraints for oracle extension, one of
which is now empirically measured rather than projected: (EC1) ancilla count and gate
count grow linearly in the number of conditions k, confirmed by gate-level simulation
at small scale (N=256, k up to 8), while circuit depth remained constant across k in
this construction due to qubit-level parallelism across conditions; (EC2) ETL
denormalisation fidelity requirements; and (EC3) QRAM dependency for datasets
exceeding N > 10^6.
```

---

## What I'd suggest trimming (you said sections can go)

- **Section 4.11's hypothetical arithmetic** (Case A/B/C with assumed $C_{eval}=1\mu s$,
  $C_{oracle}=10\mu s$) can now be shortened, since Table~\ref{tab:indexed-baseline}
  gives you a *real* $C_{eval}$ instead of an assumed one. I'd keep the crossover-point
  reasoning but cut the three manually-worked cases down to one, and cite the measured
  table for the constant instead of asserting it.
- **Section 4.12** ("We propose the following experimental design for the paper...")
  still describes an unexecuted 1M–1B record study. Given it already caused reviewer
  confusion about tense/status, consider folding its content into Future Work (FW1/FW2)
  as a single paragraph rather than keeping it as a standalone six-part subsection —
  it's currently redundant with Section 5.7's table.

---

## Files in this package

- `quantum_oracle_experiment.py` — full source (Experiments A and B), runs in under a
  minute on a laptop, numpy-only dependency.
- `exp_a_results.json` / `exp_a_results.csv` — full gate-level oracle results.
- `exp_b_results.json` / `exp_b_results.csv` — full classical-baseline timing results.

Add these to the GitHub replication package (and fix its public-accessibility issue,
still outstanding from the first review round) alongside the existing Q#/C# code.
