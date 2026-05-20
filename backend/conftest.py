import sys
import os

# Ensure the backend directory is on sys.path so that `agents`, `tools`, `rag`, etc. are importable
sys.path.insert(0, os.path.dirname(__file__))
