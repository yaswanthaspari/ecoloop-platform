"""
EcoLoop Root Seed Launcher
Allows running `python seed.py` directly from the parent workspace directory.
"""
import sys
import os

project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SWM_project")
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

os.chdir(project_dir)

import seed

if __name__ == "__main__":
    seed.seed_database()
