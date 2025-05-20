# QuBindR - Quantum Processor Binding Service

QuBindR is a service that optimally binds quantum circuits to available quantum processors (QPUs) the QuBind QPU selection framework. It uses a constraint-based approach to match quantum circuits with QPUs based on various criteria such as fidelity, workload, and cost.

## Features

- Quantum circuit parsing from QASM format
- Constraint-based QPU matching
- Optimization based on weighted criteria (fidelity, latency, cost)
- RESTful API using FastAPI

## Installation

### Using uv (recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv if you don't have it already:

```bash
curl -sSf https://astral.sh/uv/install.sh | bash
```

2. Clone the repository:

```bash
git clone https://github.com/yourusername/qubindr.git
cd qubindr
```

3. Create a virtual environment and install dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Alternative installation with pip

```bash
pip install -e .
```

## Usage

### Starting the API server

```bash
fastapi run src/api.py --reload
```

The server will start at http://127.0.0.1:8000 by default.

### API Endpoints

- `GET /`: Root endpoint with basic information
- `GET /qpus`: Get available quantum processors
- `GET /qpus/all`: Get all quantum processors (including unavailable)
- `POST /bind`: Get optimal quantum processor for a given circuit

## Documentation

API documentation is available at http://127.0.0.1:8000/docs when the server is running.

## Development

### Project Structure

```
qubindr/
├── src/
│   ├── api.py                # FastAPI application
│   ├── circuits.py           # Circuit parsing and manipulation
│   ├── mock.py               # Mock QPU definitions
│   ├── qubind.py             # Core binding engine
│   ├── constraint_utils.py   # Utilities for constraints
│   └── qutypes.py            # Type definitions
└── README.md                 # This file
```
