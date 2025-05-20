import uuid

import qiskit
from qiskit.converters import circuit_to_dag

from .qutypes import GateType, QuantumCircuit


def parse_qasm_to_circuit(qasm_string: str) -> QuantumCircuit:
    """
    Parses an OpenQASM string into a QuantumCircuit object

    Args:
        qasm_string: OpenQASM string

    Returns:
        QuantumCircuit: Quantum circuit representation
    """

    qiskit_circuit = qiskit.QuantumCircuit.from_qasm_str(qasm_string)

    num_qubits = qiskit_circuit.num_qubits

    circuit_name = getattr(qiskit_circuit, "name", f"circuit_{str(uuid.uuid4())[:8]}")

    circuit = QuantumCircuit(name=circuit_name, qubits_required=num_qubits)

    # Calculate circuit depth using DAG (Directed Acyclic Graph) representation
    dag = circuit_to_dag(qiskit_circuit)
    circuit_depth = dag.depth()
    circuit.depth = circuit_depth

    gate_counts = {}
    for instruction, _, _ in qiskit_circuit.data:
        gate_name = instruction.name.upper()
        try:
            gate_type = GateType(gate_name)
            gate_counts[gate_type] = gate_counts.get(gate_type, 0) + 1
        except ValueError:
            pass

    circuit.gate_counts = gate_counts

    qubits_used = set()
    for _, qargs, _ in qiskit_circuit.data:
        for qubit in qargs:
            qubits_used.add(qubit._index)

    circuit.qubits_used = qubits_used

    measurements = {}
    for instruction, qargs, _ in qiskit_circuit.data:
        if instruction.name == "measure":
            qubit_idx = qargs[0]._index
            measurements[qubit_idx] = measurements.get(qubit_idx, 0) + 1

    circuit.measurements = measurements

    return circuit
