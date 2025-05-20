import math
from typing import Any, Dict, List, Optional

try:
    from qubindr.src.qutypes import (
        Constraint,
        ConstraintOperator,
        ConstraintTarget,
        OptimizationWeights,
        QPUResource,
        QuantumCircuit,
    )
except ImportError:
    from src.qutypes import (
        Constraint,
        ConstraintOperator,
        ConstraintTarget,
        OptimizationWeights,
        QPUResource,
        QuantumCircuit,
    )


class QuBindEngine:
    def __init__(self, qpus: List[QPUResource]):
        self.qpus = qpus

    @staticmethod
    def create_constraint(
        name: str,
        description: str,
        target: str,
        property: str,
        operator: str,
        value: Any,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Constraint:
        """
        Factory method to create constraints more easily

        Args:
            name: Name of the constraint
            description: Description of the constraint
            target: Target of the constraint (qpu, circuit, or computed)
            property: Property to check
            operator: Operator to use for comparison
            value: Value to compare against
            parameters: Additional parameters

        Returns:
            Constraint: A new constraint object
        """
        return Constraint(
            name=name,
            description=description,
            target=ConstraintTarget(target),
            property=property,
            operator=ConstraintOperator(operator),
            value=value,
            parameters=parameters or {},
        )

    def matching_phase(
        self, circuit: QuantumCircuit, constraints: List[Constraint]
    ) -> List[QPUResource]:
        """Phase 1: Filter QPUs based on constraints"""
        feasible_qpus = []

        for qpu in self.qpus:
            if self._is_feasible(qpu, circuit, constraints):
                feasible_qpus.append(qpu)

        return feasible_qpus

    def _is_feasible(
        self, qpu: QPUResource, circuit: QuantumCircuit, constraints: List[Constraint]
    ) -> bool:
        """Check if QPU satisfies all constraints"""
        if not qpu.available:
            return False

        if qpu.qubits < circuit.qubits_required:
            return False

        for constraint in constraints:
            try:
                if not constraint.evaluate(qpu, circuit, self):
                    return False
            except Exception as e:
                print(f"Error evaluating constraint {constraint.name}: {str(e)}")
                return False

        return True

    def optimization_phase(
        self,
        feasible_qpus: List[QPUResource],
        circuit: QuantumCircuit,
        weights: OptimizationWeights,
    ) -> QPUResource:
        """Phase 2: Select optimal QPU based on FoM"""
        if not feasible_qpus:
            raise ValueError("No feasible QPUs found")

        best_qpu = None
        best_fom = float("inf")

        for qpu in feasible_qpus:
            fom = self._calculate_figure_of_merit(qpu, circuit, weights)
            if fom < best_fom:
                best_fom = fom
                best_qpu = qpu

        return best_qpu

    def _normalize_cost(self, cost: float) -> float:
        """Normalize cost to a value between 0 and 1

        A higher cost results in a value closer to 1.
        """
        return 1 / (1 + math.exp(-0.01 * (cost - 100)))

    def _calculate_fidelity(self, qpu: QPUResource, circuit: QuantumCircuit) -> float:
        """Calculate the expected circuit fidelity based on gate and readout fidelities"""
        if not circuit.gate_counts:
            return 1.0

        gate_fidelity = 1.0
        for gate_type, count in circuit.gate_counts.items():
            if gate_type in qpu.gate_fidelities:
                gate_fidelity *= qpu.gate_fidelities[gate_type] ** count

        readout_fidelity = 1.0
        for qubit, measurements in circuit.measurements.items():
            if qubit in qpu.readout_fidelities:
                readout_fidelity *= qpu.readout_fidelities[qubit] ** measurements

        return gate_fidelity * readout_fidelity

    def _normalize_workload(self, workload: int) -> float:
        """Normalize workload to a value between 0 and 1

        A higher workload results in a value closer to 1.
        """
        return min(1.0, workload / 100.0)

    def _calculate_figure_of_merit(
        self, qpu: QPUResource, circuit: QuantumCircuit, weights: OptimizationWeights
    ) -> float:
        """Calculate the Figure of Merit"""
        cost = self._normalize_cost(self._calculate_cost(qpu, circuit))
        fidelity = self._calculate_fidelity(qpu, circuit)
        workload = self._normalize_workload(qpu.workload)

        fom = (
            weights.cost_weight * cost
            + weights.error_weight * (1 - fidelity)
            + weights.workload_weight * workload
        )

        return fom

    def _calculate_cost(self, qpu: QPUResource, circuit: QuantumCircuit) -> float:
        """Calculate the cost of running the circuit on the QPU"""
        return qpu.cost(circuit)
