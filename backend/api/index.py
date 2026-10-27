import os
import sys
# Root directory of the project
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
# Backend directory containing the FastAPI application
backend_dir = os.path.join(project_root, "backend")
if not os.path.isdir(os.path.join(backend_dir, "app")):
    raise RuntimeError(
        f"FastAPI application directory not found: {backend_dir}"
    )
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
from app.main import app