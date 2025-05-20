from typing import Any, Optional

from .qutypes import QPUResource, QuantumCircuit


def evaluate_expression(
    expression: str,
    qpu: Optional[QPUResource] = None,
    circuit: Optional[QuantumCircuit] = None,
    engine: Any = None,
) -> Any:
    """
    Evaluate a complex constraint expression that may reference QPU or circuit properties.

    Supports basic expressions like:
    - qpu.max_depth
    - circuit.depth
    - qpu.max_depth * 0.8
    - circuit.depth * 2
    - qpu.gate_fidelities.CNOT > 0.99

    Args:
        expression: String expression to evaluate
        qpu: QPU resource object
        circuit: Quantum circuit object
        engine: Optional QuBindEngine for computed properties

    Returns:
        The evaluated result of the expression
    """
    # Simple direct property access
    if expression.startswith("qpu.") and qpu:
        prop_path = expression[4:]  # Remove "qpu." prefix
        return get_nested_property(qpu, prop_path)

    elif expression.startswith("circuit.") and circuit:
        prop_path = expression[8:]  # Remove "circuit." prefix
        return get_nested_property(circuit, prop_path)

    elif expression.startswith("computed.") and engine and qpu and circuit:
        prop_name = expression[9:]  # Remove "computed." prefix
        if prop_name == "fidelity":
            return engine._calculate_fidelity(qpu, circuit)
        elif prop_name == "cost":
            return qpu.cost(circuit)
        elif prop_name == "normalized_cost":
            return engine._normalize_cost(qpu.cost(circuit))
        elif prop_name == "normalized_workload":
            return engine._normalize_workload(qpu.workload)
        elif prop_name == "circuit_depth":
            return circuit.depth
        else:
            raise ValueError(f"Computed property {prop_name} not supported")

    # For more complex expressions, we'd need a proper expression parser
    # This is a simplified approach for common cases

    # Handle multiplication expressions like "qpu.max_depth * 0.8"
    if " * " in expression:
        parts = expression.split(" * ")
        if len(parts) == 2:
            left = evaluate_expression(parts[0].strip(), qpu, circuit, engine)
            try:
                right = float(parts[1].strip())
                return left * right
            except ValueError:
                right = evaluate_expression(parts[1].strip(), qpu, circuit, engine)
                return left * right

    # Handle division expressions like "circuit.qubits_required / 2"
    if " / " in expression:
        parts = expression.split(" / ")
        if len(parts) == 2:
            left = evaluate_expression(parts[0].strip(), qpu, circuit, engine)
            try:
                right = float(parts[1].strip())
                return left / right
            except ValueError:
                right = evaluate_expression(parts[1].strip(), qpu, circuit, engine)
                return left / right

    # Handle addition expressions
    if " + " in expression:
        parts = expression.split(" + ")
        if len(parts) == 2:
            left = evaluate_expression(parts[0].strip(), qpu, circuit, engine)
            try:
                right = float(parts[1].strip())
                return left + right
            except ValueError:
                right = evaluate_expression(parts[1].strip(), qpu, circuit, engine)
                return left + right

    # Handle subtraction expressions
    if " - " in expression:
        parts = expression.split(" - ")
        if len(parts) == 2:
            left = evaluate_expression(parts[0].strip(), qpu, circuit, engine)
            try:
                right = float(parts[1].strip())
                return left - right
            except ValueError:
                right = evaluate_expression(parts[1].strip(), qpu, circuit, engine)
                return left - right

    # If it's a literal value, try to convert it
    try:
        # Try to convert to int first
        return int(expression)
    except ValueError:
        try:
            # Then try float
            return float(expression)
        except ValueError:
            # If not a number, return as is
            return expression


def get_nested_property(obj: Any, property_path: str) -> Any:
    """
    Get a property from an object using a dot-notation path.

    Args:
        obj: Object to get property from
        property_path: Path to the property using dot notation (e.g., "gate_fidelities.CNOT")

    Returns:
        The property value
    """
    if "." in property_path:
        parts = property_path.split(".")
        current = obj
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise ValueError(f"Property {property_path} not found in object")
        return current
    else:
        if hasattr(obj, property_path):
            return getattr(obj, property_path)
        else:
            raise ValueError(f"Property {property_path} not found in object")
