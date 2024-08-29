from django.shortcuts import render
from django.http import JsonResponse
import numpy as np
from qiskit_aer import Aer
from qiskit import QuantumCircuit, transpile
from collections import Counter
import math
import base64
from django.http import HttpResponse



def bits_to_bytes(bits):
    while len(bits) % 8 != 0:
        bits += '0'
    byte_array = bytearray(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    return bytes(byte_array)

def calculate_entropy(bit_string):
    length = len(bit_string)
    frequency = Counter(bit_string)
    entropy = -sum((count / length) * math.log2(count / length) for count in frequency.values())
    return entropy

def generate_quantum_key(request):
    num_qubits = 16
    qc = QuantumCircuit(num_qubits, num_qubits)

    for i in range(num_qubits):
        qc.h(i)
    
    for i in range(num_qubits):
        for j in range(i + 1, num_qubits):
            qc.cx(i, j)

    for i in range(num_qubits):
        for j in range(i):
            qc.cx(i, j)
        
    qc.measure(range(num_qubits), range(num_qubits))
    simulator = Aer.get_backend('qasm_simulator')
    qc_transpiled = transpile(qc, simulator)
    shots = 16
    result = simulator.run(qc_transpiled, shots=shots).result()
    counts = result.get_counts()
    concatenated_bits = ''.join(counts.keys())
    concatenated_bits = concatenated_bits.ljust(256, '0')[:256]

    byte_data = bits_to_bytes(concatenated_bits)
    entropy_value = calculate_entropy(concatenated_bits)
    base64_key = base64.b64encode(byte_data).decode('utf-8')

    return JsonResponse({'key': base64_key, 'entropy': entropy_value})


def show_qrng_page(request):
    return render(request, 'qrng.html')