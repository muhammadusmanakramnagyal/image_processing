import numpy as np
from django.http import JsonResponse
from django.views.generic import TemplateView
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
from qiskit_aer.noise import pauli_error, NoiseModel, reset_error
from collections import Counter
from django.shortcuts import render
from django.conf import settings
def walsh_transform(vec):
    n = len(vec)
    if n == 1:
        return vec
    else:
        even = walsh_transform(vec[:n // 2])
        odd = walsh_transform(vec[n // 2:])
        return np.concatenate([even + odd, even - odd])

def nonlinearity(s_box):
    n = len(s_box)
    if n != 256:
        raise ValueError(f"Expected s_box length of 256, got {n}")
    max_nonlinearity = 0
    
    for i in range(8):
        truth_table = [(s_box[j] >> i) & 1 for j in range(n)]
        walsh_spectrum = walsh_transform(np.array(truth_table) * 2 - 1)
        max_nonlinearity = max(max_nonlinearity, 128 - np.max(np.abs(walsh_spectrum)) // 2)
    
    return max_nonlinearity

def generate_quantum_sbox(request):
    
    qc = QuantumCircuit(17, 8)  # 17 qubits and 8 classical bits
    for qubit in range(8):
        qc.rx(np.pi/2, qubit)         # Apply Rx(pi/2) gate to each qubit
        qc.ry(3*np.pi/2, qubit)       # Apply Ry(3*pi/2) gate to each qubit
        qc.rz(np.pi, qubit)           # Apply Rz(pi) gate to each qubit

    for qubit in range(8, 16):
        qc.u(np.pi/2, 0, np.pi, qubit)

    # Step 1: Define the reset probabilities
    prob0 = 0.9  # Probability of not resetting to |0⟩

    # Step 1: Define the error probabilities
    phase_flip_error_rate_rx = 0.5  # Probability of phase flip error for Rx(pi/2)
    phase_flip_error_rate_ry = 0.5  # Probability of phase flip error for Ry(3*pi/2)
    phase_flip_error_rate_rz = 0.5  # Probability of phase flip error for Rz(pi)

    # Step 2: Create phase flip error channels using pauli_error function
    phase_flip_error_rx = pauli_error([('Z', phase_flip_error_rate_rx), ('I', 1 - phase_flip_error_rate_rx)])
    phase_flip_error_ry = pauli_error([('Z', phase_flip_error_rate_ry), ('I', 1 - phase_flip_error_rate_ry)])
    phase_flip_error_rz = pauli_error([('Z', phase_flip_error_rate_rz), ('I', 1 - phase_flip_error_rate_rz)])

    reset_channel = reset_error(prob0)

    # Step 3: Create a noise model and add the phase flip error channels to it
    noise_model = NoiseModel()
    for qubit in range(8):
        noise_model.add_quantum_error(phase_flip_error_rx, 'rx', [qubit])  # Apply to each qubit for Rx(pi/2)
        noise_model.add_quantum_error(phase_flip_error_ry, 'ry', [qubit])  # Apply to each qubit for Ry(3*pi/2)
        noise_model.add_quantum_error(phase_flip_error_rz, 'rz', [qubit])  # Apply to each qubit for Rz(pi)

    for qubit in range(16):
        noise_model.add_quantum_error(reset_channel, 'reset', [qubit])  # Apply reset error to qubits

    # Perform the XOR operations
    qc.barrier()
    qc.cy(0, 16)
    qc.cy(8, 16)
    qc.reset(0)
    qc.reset(8)

    qc.barrier()
    qc.cy(1, 0)
    qc.cy(9, 0)
    qc.reset(1)
    qc.reset(9)

    qc.barrier()
    qc.cy(2, 8)
    qc.cy(10, 8)
    qc.reset(2)
    qc.reset(10)

    qc.barrier()
    qc.cy(3, 1)
    qc.cy(11, 1)
    qc.reset(3)
    qc.reset(11)

    qc.barrier()
    qc.cy(4, 9)
    qc.cy(12, 9)
    qc.reset(4)
    qc.reset(12)

    qc.barrier()
    qc.cy(5, 2)
    qc.cy(13, 2)
    qc.reset(5)
    qc.reset(13)

    qc.barrier()
    qc.cy(6, 10)
    qc.cy(14, 10)
    qc.reset(6)
    qc.reset(14)

    qc.barrier()
    qc.cy(7, 3)
    qc.cy(15, 3)
    qc.reset(7)
    qc.reset(15)
    qc.barrier()

    qc.measure([16, 0, 8, 1, 9, 2, 10, 3], [0, 1, 2, 3, 4, 5, 6, 7])

    # Compile the quantum circuit to be compatible with the backend
    simulator = Aer.get_backend('qasm_simulator')
    qc_transpiled = transpile(qc, simulator)

    # Run the transpiled quantum circuit on the simulator
    shots = 3000
    result = simulator.run(qc_transpiled, noise_model=noise_model, shots=shots).result()

    # Get and print the counts
    counts = result.get_counts()

    # Convert binary outcomes to integers and print the list
    int_counts = [int(outcome, 2) for outcome in counts.keys()]
    # Calculate nonlinearity
    s_box = int_counts
    settings.GLOBAL_SBOX=s_box

    nonlinearity_value = nonlinearity(s_box)
    # Convert nonlinearity_value to a native Python int
    nonlinearity_value = str(nonlinearity_value)
    
    return JsonResponse({'nonlinearity': nonlinearity_value})


def show_sbox_page(request):
    return render(request, 'sbox.html')

class IndexPageView(TemplateView):
    template_name = 'index.html'

