from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .circuits import parse_qasm_to_circuit
from .mock import create_mock_qpus
from .qubind import QuBindEngine
from .qutypes import BindingResult, OptimizationWeights

QPUS = create_mock_qpus()
qubind = QuBindEngine(QPUS)

app = FastAPI(
    title="QuBindR API",
    description="by adrián romero flores.",
    version="0.0.0",
)


@app.get("/", summary="Root Endpoint", tags=["Root"])
def read_root():
    """
    Returns a welcome message and API information.
    """
    return {
        "message": "Welcome to the QuBindr API!",
        "version": app.version,
        "available_qpus": len([qpu for qpu in QPUS if qpu.available]),
        "total_qpus": len(QPUS),
        "docs_url": "/docs",
    }


@app.get("/qpus", summary="Get Available Quantum Processors", tags=["QPU"])
def get_qpus():
    """
    Get the list of available quantum processors.

    Returns:
        List[QPUResource]: List of available quantum processors.
    """
    return [qpu for qpu in QPUS if qpu.available]


@app.get("/qpus/all", summary="Get All Quantum Processors", tags=["QPU"])
def get_all_qpus():
    """
    Get the list of all quantum processors, including unavailable ones.

    Returns:
        List[QPUResource]: List of all quantum processors.
    """
    return QPUS


class ConstraintRequest(BaseModel):
    name: str
    description: str
    target: str
    property: str
    operator: str
    value: Any
    parameters: Optional[Dict[str, Any]] = None


class BindRequest(BaseModel):
    qasm: str
    shots: int = 1024
    constraints: List[ConstraintRequest] = []
    figures_of_merit: Dict[str, float] = {
        "cost_weight": 0.33,
        "error_weight": 0.33,
        "workload_weight": 0.34,
    }
    ranking: bool = Field(
        default=False,
        description="If True, returns a ranked list of all feasible QPUs sorted by figure of merit"
    )


@app.post("/bind", summary="Get Optimal Quantum Processors", tags=["QPU"])
def bind_qpus(request: BindRequest):
    """
    Given a circuit, a number of shots, a set of constraints, and the figures of merit to take into account.
    
    The ranking parameter controls whether the response will include only the optimal QPU (default)
    or a complete ranked list of all feasible QPUs.

    Returns:
        BindingResult: The selected QPU and its figure of merit. If ranking is enabled, also returns ranked list of feasible QPUs.
    """
    try:
        circuit = parse_qasm_to_circuit(request.qasm)
        circuit.shots = request.shots

        print(circuit)

        constraints = []
        for constraint_req in request.constraints:
            constraint = qubind.create_constraint(
                name=constraint_req.name,
                description=constraint_req.description,
                target=constraint_req.target,
                property=constraint_req.property,
                operator=constraint_req.operator,
                value=constraint_req.value,
                parameters=constraint_req.parameters,
            )
            constraints.append(constraint)

        figures_of_merit = OptimizationWeights(
            cost_weight=request.figures_of_merit.get("cost_weight", 0.33),
            error_weight=request.figures_of_merit.get("error_weight", 0.33),
            workload_weight=request.figures_of_merit.get("workload_weight", 0.34),
        )

        feasible_qpus = qubind.matching_phase(circuit, constraints)

        if not feasible_qpus:
            raise HTTPException(
                status_code=404,
                detail="No feasible QPUs found for the given constraints",
            )

        if not request.figures_of_merit:
            selected_qpu = feasible_qpus[0]
            
            if request.ranking:
                # When no figures of merit are given but ranking is requested, 
                # return all feasible QPUs as ranked
                ranked_qpus = []
                for qpu in feasible_qpus:
                    ranked_qpus.append({
                        "qpu_id": qpu.id,
                        "qpu_name": qpu.name,
                        "provider": qpu.provider,
                        "figure_of_merit": 0.0  # No figure of merit calculation
                    })
                return BindingResult(
                    selected_qpu=selected_qpu, 
                    figure_of_merit=0.0,
                    ranked_qpus=ranked_qpus
                )
            else:
                # No ranking requested, just return the first feasible QPU
                return BindingResult(selected_qpu=selected_qpu, figure_of_merit=0.0)

        optimal_qpu = qubind.optimization_phase(
            feasible_qpus, circuit, figures_of_merit
        )
        
        # Calculate the figure of merit for the optimal QPU
        fom = qubind._calculate_figure_of_merit(optimal_qpu, circuit, figures_of_merit)
        
        if request.ranking:
            # Generate ranked list of QPUs with their figures of merit
            ranked_qpus = []
            for qpu in feasible_qpus:
                qpu_fom = qubind._calculate_figure_of_merit(qpu, circuit, figures_of_merit)
                ranked_qpus.append({
                    "qpu_id": qpu.id,
                    "qpu_name": qpu.name,
                    "provider": qpu.provider,
                    "figure_of_merit": float(qpu_fom)
                })
            # Sort by figure of merit (lower is better)
            ranked_qpus.sort(key=lambda x: x["figure_of_merit"])
            return BindingResult(
                selected_qpu=optimal_qpu, 
                figure_of_merit=float(fom),
                ranked_qpus=ranked_qpus
            )
        
        return BindingResult(selected_qpu=optimal_qpu, figure_of_merit=float(fom))

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error in binding process: {str(e)}"
        )
