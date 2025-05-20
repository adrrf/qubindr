import math
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, PrivateAttr


class QPUProvider(str, Enum):
    IBM = "IBM"
    AZURE = "AZURE"
    AWS = "AWS"


class GateType(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"
    H = "H"
    CNOT = "CNOT"
    CZ = "CZ"
    RZ = "RZ"
    RX = "RX"
    RY = "RY"
    T = "T"
    S = "S"


class QuantumCircuit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    qubits_required: int = Field(
        ..., gt=0, description="Number of logical qubits required"
    )
    shots: int = Field(default=1000, gt=0, description="Number of shots for execution")
    gate_counts: Dict[GateType, int] = Field(
        default_factory=dict, description="Gate counts after transpilation"
    )
    depth: int = Field(
        default=0, ge=0, description="Circuit depth (longest path)"
    )
    qubits_used: Set[int] = Field(
        default_factory=set, description="Set of qubits used in circuit"
    )
    measurements: Dict[int, int] = Field(
        default_factory=dict, description="Measurements per qubit"
    )


class QPUResource(BaseModel):
    id: str
    name: str
    provider: QPUProvider
    qubits: int = Field(..., gt=0, description="Number of physical qubits")
    native_gates: Set[GateType] = Field(..., description="Set of native gates")
    gate_fidelities: Dict[GateType, float] = Field(
        ..., description="Fidelity for each gate type"
    )
    readout_fidelities: Dict[int, float] = Field(
        ..., description="Readout fidelity per qubit"
    )
    max_depth: int = Field(default=1000, gt=0, description="Maximum circuit depth supported")
    max_shots: int = Field(default=10000, gt=0, description="Maximum number of shots supported")
    workload: int = Field(default=0, ge=0, description="Number of pending jobs")
    available: bool = Field(default=True, description="Operational status")
    _cost_fn: Callable[..., float] = PrivateAttr()

    def __init__(self, **data):
        cost_fn = data.pop("cost", None)
        if not callable(cost_fn):
            raise ValueError("A callable 'cost' function must be provided.")
        super().__init__(**data)
        self._cost_fn = cost_fn

    def cost(self, *args, **kwargs) -> float:
        return self._cost_fn(*args, **kwargs)


class OptimizationWeights(BaseModel):
    cost_weight: float = Field(default=0.33, ge=0, le=1, description="Weight for cost factor in figure of merit")
    error_weight: float = Field(default=0.33, ge=0, le=1, description="Weight for error factor in figure of merit")
    workload_weight: float = Field(default=0.34, ge=0, le=1, description="Weight for workload factor in figure of merit")

    def model_post_init(self, __context: Any) -> None:
        total = self.cost_weight + self.error_weight + self.workload_weight
        if not math.isclose(total, 1.0, rel_tol=1e-6):
            raise ValueError(f"Weights must sum to 1.0, got {total}")


class ConstraintOperator(str, Enum):
    """Operators for constraints"""

    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GE = "ge"  # Greater than or equal
    LT = "lt"  # Less than
    LE = "le"  # Less than or equal
    IN = "in"  # In set/list
    NOT_IN = "not_in"  # Not in set/list
    CONTAINS = "contains"  # Contains all elements
    SUBSET = "subset"  # Is subset
    SUPERSET = "superset"  # Is superset


class ConstraintTarget(str, Enum):
    """Targets for constraints"""

    QPU = "qpu"  # Target QPU property
    CIRCUIT = "circuit"  # Target circuit property
    COMPUTED = "computed"  # Target computed value (e.g., fidelity)


class Constraint(BaseModel):
    name: str
    description: str
    target: ConstraintTarget = Field(default=ConstraintTarget.QPU)
    property: str = Field(..., description="Property name to check")
    operator: ConstraintOperator = Field(default=ConstraintOperator.GE)
    value: Any = Field(..., description="Value to compare against")
    custom_fn: Optional[Callable[[QPUResource, QuantumCircuit], bool]] = Field(
        default=None, description="Optional custom constraint function"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional parameters"
    )

    def evaluate(
        self, qpu: "QPUResource", circuit: "QuantumCircuit", engine: Any = None
    ) -> bool:
        """
        Evaluate the constraint for the given QPU and circuit

        Args:
            qpu: The QPU to evaluate
            circuit: The circuit to evaluate
            engine: Optional QuBindEngine instance for computed properties

        Returns:
            bool: True if the constraint is satisfied, False otherwise
        """
        # Import here to avoid circular imports
        from .constraint_utils import evaluate_expression, get_nested_property
        
        # If custom function is provided, use it
        if self.custom_fn:
            return self.custom_fn(qpu, circuit)

        # Get the property value based on target
        if self.target == ConstraintTarget.QPU:
            property_value = get_nested_property(qpu, self.property)
        elif self.target == ConstraintTarget.CIRCUIT:
            property_value = get_nested_property(circuit, self.property)
        elif self.target == ConstraintTarget.COMPUTED:
            # Handle computed properties that require the engine
            if not engine:
                raise ValueError("Engine required for computed properties")

            if self.property == "fidelity":
                property_value = engine._calculate_fidelity(qpu, circuit)
            elif self.property == "cost":
                property_value = qpu.cost(circuit)
            elif self.property == "normalized_cost":
                property_value = engine._normalize_cost(qpu.cost(circuit))
            elif self.property == "normalized_workload":
                property_value = engine._normalize_workload(qpu.workload)
            elif self.property == "circuit_depth":
                property_value = circuit.depth
            else:
                raise ValueError(f"Computed property {self.property} not supported")
        else:
            raise ValueError(f"Unknown target: {self.target}")

        # Evaluate the comparison value if it's an expression
        comparison_value = self.value
        if isinstance(comparison_value, str) and any(x in comparison_value for x in ["qpu.", "circuit.", "computed."]):
            comparison_value = evaluate_expression(comparison_value, qpu, circuit, engine)

        # Apply the operator
        if self.operator == ConstraintOperator.EQ:
            return property_value == comparison_value
        elif self.operator == ConstraintOperator.NE:
            return property_value != comparison_value
        elif self.operator == ConstraintOperator.GT:
            return property_value > comparison_value
        elif self.operator == ConstraintOperator.GE:
            return property_value >= comparison_value
        elif self.operator == ConstraintOperator.LT:
            return property_value < comparison_value
        elif self.operator == ConstraintOperator.LE:
            return property_value <= comparison_value
        elif self.operator == ConstraintOperator.IN:
            return property_value in comparison_value
        elif self.operator == ConstraintOperator.NOT_IN:
            return property_value not in comparison_value
        elif self.operator == ConstraintOperator.CONTAINS:
            return all(item in property_value for item in comparison_value)
        elif self.operator == ConstraintOperator.SUBSET:
            return set(property_value).issubset(set(comparison_value))
        elif self.operator == ConstraintOperator.SUPERSET:
            return set(property_value).issuperset(set(comparison_value))
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

    class Config:
        arbitrary_types_allowed = True


class BindingRequest(BaseModel):
    qasm: str = Field(..., description="OpenQASM string defining the circuit")
    shots: int = Field(default=1024, ge=1, description="Number of shots")
    constraints: List[Constraint] = Field(default_factory=list)
    weights: OptimizationWeights = Field(default_factory=OptimizationWeights)


class BindingResult(BaseModel):
    selected_qpu: QPUResource
    figure_of_merit: float
    ranked_qpus: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Ranked list of QPUs with their figures of merit when ranking is enabled"
    )
