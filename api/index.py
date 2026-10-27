import os
import sys

cur_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(cur_dir, "..", "backend")
if os.path.exists(backend_dir) and backend_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(backend_dir))

from app.main import app
