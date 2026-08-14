"""
Experiment A: gate-level, reversible multi-condition Grover oracle (state-vector simulation)
Experiment B: indexed classical baseline (hash lookup / binary search) vs linear scan

Both experiments are self-contained, dependency-free (numpy only), and reproducible.
"""
import numpy as np
import time
import bisect
import random
import json
import math

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# Experiment A: gate-level reversible multi-condition oracle
# ---------------------------------------------------------------------------

class Circuit:
    """Minimal state-vector simulator with gate/qubit bookkeeping for depth analysis."""
    def __init__(self, n_qubits):
        self.n = n_qubits
        self.dim = 1 << n_qubits
        self.state = np.zeros(self.dim, dtype=np.complex128)
        self.state[0] = 1.0
        self.gate_log = []          # (gate_type, qubits_touched)
        self.qubit_layer = [0] * n_qubits  # for depth computation

    def _log(self, gate_type, qubits):
        self.gate_log.append((gate_type, tuple(qubits)))
        layer = max(self.qubit_layer[q] for q in qubits) + 1
        for q in qubits:
            self.qubit_layer[q] = layer

    def h(self, q):
        idx = np.arange(self.dim)
        bit = (idx >> q) & 1
        mask0 = idx[bit == 0]
        mask1 = mask0 | (1 << q)
        a0 = self.state[mask0]
        a1 = self.state[mask1]
        inv_sqrt2 = 1 / math.sqrt(2)
        self.state[mask0] = (a0 + a1) * inv_sqrt2
        self.state[mask1] = (a0 - a1) * inv_sqrt2
        self._log("H", [q])

    def x(self, q):
        idx = np.arange(self.dim)
        bit = (idx >> q) & 1
        mask0 = idx[bit == 0]
        mask1 = mask0 | (1 << q)
        tmp = self.state[mask0].copy()
        self.state[mask0] = self.state[mask1]
        self.state[mask1] = tmp
        self._log("X", [q])

    def mcx(self, controls, target):
        """Multi-controlled X: flip `target` iff all `controls` bits are 1."""
        idx = np.arange(self.dim)
        cond = np.ones(self.dim, dtype=bool)
        for c in controls:
            cond &= ((idx >> c) & 1) == 1
        target_bit0 = ((idx >> target) & 1) == 0
        idx0 = idx[cond & target_bit0]
        idx1 = idx0 | (1 << target)
        tmp = self.state[idx0].copy()
        self.state[idx0] = self.state[idx1]
        self.state[idx1] = tmp
        gate_type = "TOFFOLI" if len(controls) == 2 else ("CNOT" if len(controls) == 1 else f"MCX{len(controls)}")
        self._log(gate_type, list(controls) + [target])

    def prob_index_equals(self, index_qubits, value):
        """Probability that the index register (given qubit list, LSB-first) reads `value`."""
        idx = np.arange(self.dim)
        mask = np.ones(self.dim, dtype=bool)
        for i, q in enumerate(index_qubits):
            bit = (value >> i) & 1
            mask &= ((idx >> q) & 1) == bit
        return float(np.sum(np.abs(self.state[mask]) ** 2))

    def sample_index(self, index_qubits, n_index_bits, rng):
        probs = np.abs(self.state) ** 2
        outcome = rng.choice(self.dim, p=probs / probs.sum())
        val = 0
        for i, q in enumerate(index_qubits):
            bit = (outcome >> q) & 1
            val |= (bit << i)
        return val

    def depth(self):
        return max(self.qubit_layer) if self.qubit_layer else 0

    def gate_counts(self):
        counts = {}
        for gtype, _ in self.gate_log:
            counts[gtype] = counts.get(gtype, 0) + 1
        return counts


def build_field_layout(n_index, k):
    """Partition a FIXED n_index-bit index register into k conditions (near-equal field
    widths). N = 2^n_index is held constant across k, isolating oracle cost vs. k."""
    base = n_index // k
    rem = n_index % k
    fields = []
    pos = 0
    for j in range(k):
        w = base + (1 if j < rem else 0)
        if w < 1:
            raise ValueError(f"n_index={n_index} too small to support k={k} conditions")
        fields.append(list(range(pos, pos + w)))
        pos += w
    return fields


def apply_oracle(circ, fields, targets, condition_ancillas, phase_ancilla):
    """Reversible oracle: phase-flips the unique index whose k fields match `targets`.
    `fields[j]` is a list of qubit indices (any width); `targets[j]` is an int whose
    low len(fields[j]) bits give the target pattern for that field."""
    for field_qubits, tval, anc in zip(fields, targets, condition_ancillas):
        flip_qubits = [q for i, q in enumerate(field_qubits) if ((tval >> i) & 1) == 0]
        for q in flip_qubits:
            circ.x(q)
        circ.mcx(field_qubits, anc)
        for q in flip_qubits:
            circ.x(q)
    circ.mcx(condition_ancillas, phase_ancilla)
    for field_qubits, tval, anc in zip(fields, targets, condition_ancillas):
        flip_qubits = [q for i, q in enumerate(field_qubits) if ((tval >> i) & 1) == 0]
        for q in flip_qubits:
            circ.x(q)
        circ.mcx(field_qubits, anc)
        for q in flip_qubits:
            circ.x(q)


def apply_diffusion(circ, index_qubits):
    for q in index_qubits:
        circ.h(q)
    for q in index_qubits:
        circ.x(q)
    # multi-controlled Z about |11...1> realized via ancilla-free phase trick:
    # use last index qubit as target of MCX with the rest as controls, wrapped in H
    controls = index_qubits[:-1]
    target = index_qubits[-1]
    circ.h(target)
    circ.mcx(controls, target)
    circ.h(target)
    for q in index_qubits:
        circ.x(q)
    for q in index_qubits:
        circ.h(q)


def measure_single_oracle_call(n_qubits, fields, targets, condition_ancillas, phase_ancilla):
    """Build one isolated oracle application (no diffusion, no iteration) purely to
    measure its gate count / circuit depth in isolation."""
    circ = Circuit(n_qubits)
    apply_oracle(circ, fields, targets, condition_ancillas, phase_ancilla)
    return circ.gate_counts(), circ.depth()


def measure_single_diffusion(n_qubits, index_qubits):
    circ = Circuit(n_qubits)
    apply_diffusion(circ, index_qubits)
    return circ.gate_counts(), circ.depth()


def merge_counts(a, b):
    out = dict(a)
    for k_, v in b.items():
        out[k_] = out.get(k_, 0) + v
    return out


def run_condition_experiment(n_index, k, trials=30, seed=42):
    """N = 2^n_index is FIXED across all k; only the number of conjunctive conditions
    k varies, isolating oracle construction cost from search-space-size effects."""
    fields = build_field_layout(n_index, k)
    N = 1 << n_index
    condition_ancillas = list(range(n_index, n_index + k))
    phase_ancilla = n_index + k
    n_qubits = n_index + k + 1
    index_qubits = list(range(n_index))
    theoretical_iters = max(1, math.floor((math.pi / 4) * math.sqrt(N)))
    field_widths = [len(f) for f in fields]

    # --- isolated per-component measurements (built once, deterministic target) ---
    probe_targets = [0] * k
    oracle_gates, oracle_depth = measure_single_oracle_call(
        n_qubits, fields, probe_targets, condition_ancillas, phase_ancilla)
    diffusion_gates, diffusion_depth = measure_single_diffusion(n_qubits, index_qubits)

    full_circuit_gates_total = sum(oracle_gates.values()) + sum(diffusion_gates.values())
    full_circuit_depth_per_iteration = oracle_depth + diffusion_depth

    total_circuit_gate_count = (
        n_index + 2
        + theoretical_iters * full_circuit_gates_total
    )
    total_circuit_depth = (
        1
        + theoretical_iters * full_circuit_depth_per_iteration
    )

    # --- actual functional simulation across trials (correctness / success rate) ---
    rng_local = np.random.default_rng(seed + k)
    results = []
    for t in range(trials):
        targets = [int(rng_local.integers(0, 1 << w)) for w in field_widths]
        marked_index = 0
        bitpos = 0
        for tval, w in zip(targets, field_widths):
            marked_index |= (tval << bitpos)
            bitpos += w

        circ = Circuit(n_qubits)
        for q in index_qubits:
            circ.h(q)
        circ.x(phase_ancilla)
        circ.h(phase_ancilla)

        for _ in range(theoretical_iters):
            apply_oracle(circ, fields, targets, condition_ancillas, phase_ancilla)
            apply_diffusion(circ, index_qubits)

        success_prob = circ.prob_index_equals(index_qubits, marked_index)
        sampled = circ.sample_index(index_qubits, n_index, rng_local)
        success = int(sampled == marked_index)

        results.append({
            "trial": t, "N": N, "k": k, "marked_index": marked_index,
            "oracle_calls": theoretical_iters, "success": success,
            "success_prob": success_prob,
        })

    return {
        "k": k, "N": N, "n_index_qubits": n_index, "field_widths": field_widths,
        "ancilla_qubits": k + 1, "total_qubits": n_qubits,
        "oracle_calls_theoretical": theoretical_iters,
        "gates_per_single_oracle_call": {
            "breakdown": oracle_gates, "total": sum(oracle_gates.values()), "depth": oracle_depth,
        },
        "gates_per_single_diffusion": {
            "breakdown": diffusion_gates, "total": sum(diffusion_gates.values()), "depth": diffusion_depth,
        },
        "full_circuit_totals": {
            "total_gate_count": total_circuit_gate_count,
            "total_depth": total_circuit_depth,
        },
        "mean_success_prob": float(np.mean([r["success_prob"] for r in results])),
        "empirical_success_rate": float(np.mean([r["success"] for r in results])),
        "trials": trials,
    }


# ---------------------------------------------------------------------------
# Experiment B: indexed classical baseline
# ---------------------------------------------------------------------------

def run_classical_baseline(N_values, trials=30, seed=7):
    random.seed(seed)
    out = []
    for N in N_values:
        data = list(range(N))
        d = {v: i for i, v in enumerate(data)}
        sorted_data = sorted(data)

        linear_times, hash_times, bsearch_times = [], [], []
        for _ in range(trials):
            target = random.randint(0, N - 1)

            t0 = time.perf_counter()
            idx = -1
            for i, v in enumerate(data):
                if v == target:
                    idx = i
                    break
            t1 = time.perf_counter()
            linear_times.append((t1 - t0) * 1e3)

            t0 = time.perf_counter()
            idx2 = d.get(target, -1)
            t1 = time.perf_counter()
            hash_times.append((t1 - t0) * 1e3)

            t0 = time.perf_counter()
            pos = bisect.bisect_left(sorted_data, target)
            found = pos < len(sorted_data) and sorted_data[pos] == target
            t1 = time.perf_counter()
            bsearch_times.append((t1 - t0) * 1e3)

        out.append({
            "N": N,
            "linear_scan_ms_mean": float(np.mean(linear_times)),
            "linear_scan_ms_std": float(np.std(linear_times)),
            "hash_lookup_ms_mean": float(np.mean(hash_times)),
            "hash_lookup_ms_std": float(np.std(hash_times)),
            "binary_search_ms_mean": float(np.mean(bsearch_times)),
            "binary_search_ms_std": float(np.std(bsearch_times)),
            "grover_oracle_calls_theoretical": max(1, math.floor((math.pi / 4) * math.sqrt(N))),
        })
    return out


if __name__ == "__main__":
    print("=== Experiment A: gate-level multi-condition oracle (N fixed, k varies) ===")
    N_INDEX = 8  # N = 2^8 = 256, held constant across all k (matches upper end of Table 5's range)
    exp_a_results = []
    for k in [1, 2, 4, 8]:
        r = run_condition_experiment(N_INDEX, k, trials=30)
        exp_a_results.append(r)
        print(json.dumps(r, indent=2))

    print("\n=== Experiment B: indexed classical baseline ===")
    N_values = [64, 128, 256, 512, 1024, 4096, 16384, 65536, 262144, 1048576]
    exp_b_results = run_classical_baseline(N_values, trials=30)
    for r in exp_b_results:
        print(json.dumps(r, indent=2))

    with open("/home/claude/exp_a_results.json", "w") as f:
        json.dump(exp_a_results, f, indent=2)
    with open("/home/claude/exp_b_results.json", "w") as f:
        json.dump(exp_b_results, f, indent=2)
    print("\nSaved results to exp_a_results.json and exp_b_results.json")
