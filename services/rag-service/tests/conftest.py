import os

os.environ["QDRANT_URL"] = "http://localhost:6333"

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
