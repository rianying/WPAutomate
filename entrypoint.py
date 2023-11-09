# entrypoint.py
import sys
import importlib

if len(sys.argv) < 2:
    print("Usage: entrypoint.py <script_name>")
    sys.exit(1)

script_name = sys.argv[1]

try:
    module = importlib.import_module(script_name)
    module.main()
except ModuleNotFoundError:
    print(f"Script '{script_name}' not found.")
    sys.exit(1)
