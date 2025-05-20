from typing import List

try:
    from qubindr.src.qutypes import GateType, QPUProvider, QPUResource
except ImportError:
    from src.qutypes import GateType, QPUProvider, QPUResource


def create_mock_qpus() -> List[QPUResource]:
    """Create a focused list of mock QPU resources with clear trade-offs"""
    return [
        create_premium_qpu(),
        create_standard_qpu(),
        create_budget_qpu(),
        create_capacity_qpu(),
        create_available_qpu(),
        create_inactive_qpu(),
    ]


def create_premium_qpu() -> QPUResource:
    """High-end QPU with excellent fidelity but high cost"""
    return QPUResource(
        id="premium-01",
        name="Premium Quantum",
        provider=QPUProvider.IBM,
        qubits=27,
        native_gates={
            GateType.X,
            GateType.Y,
            GateType.Z,
            GateType.H,
            GateType.CNOT,
            GateType.CZ,
            GateType.RZ,
            GateType.RX,
            GateType.RY,
        },
        gate_fidelities={
            GateType.X: 0.9995,
            GateType.Y: 0.9995,
            GateType.Z: 0.9997,
            GateType.H: 0.9990,
            GateType.CNOT: 0.995,
            GateType.CZ: 0.994,
            GateType.RZ: 0.9993,
            GateType.RX: 0.9992,
            GateType.RY: 0.9991,
        },
        readout_fidelities={i: 0.99 for i in range(27)},
        max_depth=2000,
        max_shots=20000,  # Premium tier has highest shot limit
        workload=15,
        available=True,
        cost=lambda circuit: 2.0
        * circuit.shots
        * sum(circuit.gate_counts.values())
        / 100,
    )


def create_standard_qpu() -> QPUResource:
    """Standard QPU with good balance of cost and fidelity"""
    return QPUResource(
        id="standard-01",
        name="Standard Quantum",
        provider=QPUProvider.AZURE,
        qubits=20,
        native_gates={
            GateType.X,
            GateType.Y,
            GateType.Z,
            GateType.H,
            GateType.CNOT,
            GateType.CZ,
            GateType.RZ,
        },
        gate_fidelities={
            GateType.X: 0.9980,
            GateType.Y: 0.9975,
            GateType.Z: 0.9985,
            GateType.H: 0.9970,
            GateType.CNOT: 0.988,
            GateType.CZ: 0.987,
            GateType.RZ: 0.9975,
        },
        readout_fidelities={i: 0.985 for i in range(20)},
        max_depth=1000,
        max_shots=10000,  # Standard tier with moderate shot limit
        workload=10,
        available=True,
        cost=lambda circuit: 1.0
        * circuit.shots
        * sum(circuit.gate_counts.values())
        / 100,
    )


def create_budget_qpu() -> QPUResource:
    """Budget QPU with lower fidelity but very low cost"""
    return QPUResource(
        id="budget-01",
        name="Budget Quantum",
        provider=QPUProvider.AWS,
        qubits=12,
        native_gates={GateType.X, GateType.Z, GateType.H, GateType.CNOT, GateType.RZ},
        gate_fidelities={
            GateType.X: 0.985,
            GateType.Z: 0.987,
            GateType.H: 0.982,
            GateType.CNOT: 0.975,
            GateType.RZ: 0.984,
        },
        readout_fidelities={i: 0.96 for i in range(12)},
        max_depth=500,
        max_shots=5000,  # Budget tier with lower shot limit
        workload=75,
        available=True,
        cost=lambda circuit: 0.5
        * circuit.shots
        * sum(circuit.gate_counts.values())
        / 100,
    )


def create_capacity_qpu() -> QPUResource:
    """High-capacity QPU with many qubits but medium fidelity"""
    return QPUResource(
        id="capacity-01",
        name="Capacity Quantum",
        provider=QPUProvider.IBM,
        qubits=127,  # Many qubits
        native_gates={GateType.X, GateType.Z, GateType.H, GateType.CNOT, GateType.RZ},
        gate_fidelities={
            GateType.X: 0.990,
            GateType.Z: 0.992,
            GateType.H: 0.988,
            GateType.CNOT: 0.980,
            GateType.RZ: 0.989,
        },
        readout_fidelities={i: 0.975 for i in range(127)},
        max_depth=800,
        max_shots=8000,  # Capacity-focused QPU with moderate shot limit
        workload=50,
        available=True,
        cost=lambda circuit: 1.5 * circuit.shots * len(circuit.qubits_used) / 10,
    )


def create_available_qpu() -> QPUResource:
    """High-available QPU with many qubits but medium fidelity"""
    return QPUResource(
        id="available-01",
        name="Available Quantum",
        provider=QPUProvider.AWS,
        qubits=127,  # Many qubits
        native_gates={GateType.X, GateType.Z, GateType.H, GateType.CNOT, GateType.RZ},
        gate_fidelities={
            GateType.X: 0.990,
            GateType.Z: 0.992,
            GateType.H: 0.988,
            GateType.CNOT: 0.980,
            GateType.RZ: 0.989,
        },
        readout_fidelities={i: 0.975 for i in range(127)},
        max_depth=600,
        max_shots=15000,  # Available QPU with high shot limit
        workload=5,
        available=True,
        cost=lambda circuit: 1.5 * circuit.shots * len(circuit.qubits_used) / 10,
    )


def create_inactive_qpu() -> QPUResource:
    """Inactive QPU (for testing availability constraints)"""
    return QPUResource(
        id="inactive-01",
        name="Inactive Quantum",
        provider=QPUProvider.AWS,
        qubits=20,
        native_gates={
            GateType.X,
            GateType.Y,
            GateType.Z,
            GateType.H,
            GateType.CNOT,
            GateType.RZ,
        },
        gate_fidelities={
            GateType.X: 0.990,
            GateType.Y: 0.989,
            GateType.Z: 0.991,
            GateType.H: 0.987,
            GateType.CNOT: 0.981,
            GateType.RZ: 0.988,
        },
        readout_fidelities={i: 0.975 for i in range(20)},
        max_depth=1200,
        max_shots=10000,  # Inactive QPU but still has moderate shot limit
        workload=0,
        available=False,
        cost=lambda circuit: 1.0
        * circuit.shots
        * sum(circuit.gate_counts.values())
        / 100,
    )
