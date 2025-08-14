import sys
import os

# Add the parent directory of opal_engine to the Python path
# This allows importing modules within opal_engine as if it were a package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from opal_engine.gfx import engine

if __name__ == "__main__":
    engine.main()