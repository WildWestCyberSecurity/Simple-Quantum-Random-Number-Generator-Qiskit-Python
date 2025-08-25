#!/usr/bin/env python3
# IBM Quantum Platform QRNG (Open plan, ISA-compliant)
# Prints: hack the planet {<qrng_value>}

import os, sys
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

TOKEN    = os.getenv("IBM_QUANTUM_TOKEN", "").strip()
INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE", "").strip() or None
BACKEND  = os.getenv("IBM_BACKEND", "").strip() or None
N_BITS   = int(os.getenv("QRNG_BITS", "32"))
VERBOSE  = bool(int(os.getenv("QRNG_VERBOSE", "1")))

if not TOKEN:
    sys.exit("Missing IBM_QUANTUM_TOKEN (Platform token).")

service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=TOKEN,
    instance=INSTANCE,
)

backend = service.backend(BACKEND) if BACKEND else service.least_busy(operational=True, simulator=False)
if VERBOSE:
    print(f"[info] backend: {backend.name}")

# 1-qubit QRNG: prepare |+> then measure (1 random bit per shot)
qc = QuantumCircuit(1)
qc.h(0)
qc.measure_all()

# *** Critical: transpile to the backend's basis gates (ISA) ***
tqc = transpile(qc, backend=backend, optimization_level=1)

shots = max(1, N_BITS)
sampler = SamplerV2(mode=backend)          # backend (job) mode → OK on Open plan
job = sampler.run([tqc], shots=shots)      # run transpiled circuit
result = job.result()
pub = result[0]

# Extract per-shot bitstrings ("0"/"1"), pack big-endian → int
bitstrings = pub.data.meas.get_bitstrings()
if len(bitstrings) < N_BITS:
    sys.exit(f"Received {len(bitstrings)} bits, expected {N_BITS}")

val = 0
for b in bitstrings[:N_BITS]:
    val = (val << 1) | (1 if b == "1" else 0)

if VERBOSE:
    ones = sum(1 for b in bitstrings[:N_BITS] if b == "1")
    zeros = N_BITS - ones
    print(f"[info] collected {N_BITS} bits: zeros={zeros}, ones={ones}")

print(f"hack the planet {{{val}}}")
