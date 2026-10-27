import os
import sys

cur_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(cur_dir)
backend_dir = os.path.join(project_root, "backend")

# Support both possible layouts:
# 1. api/index.py and app/ in the same directory
# 2. api/index.py and backend/app/
if os.path.isdir(os.path.join(cur_dir, "app")):
    app_dir = cur_dir
elif os.path.isdir(os.path.join(backend_dir, "app")):
    app_dir = backend_dir
else:
    raise RuntimeError(
        "Cannot find the FastAPI app directory. "
        f"Checked {cur_dir} and {backend_dir}"
    )

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.main import app