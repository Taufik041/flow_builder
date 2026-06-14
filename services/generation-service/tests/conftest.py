import os

os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["RAG_SERVICE_URL"] = "http://localhost:8002"

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
