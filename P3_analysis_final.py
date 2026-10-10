"""Revised entry point; legacy implementation is archived."""
from pathlib import Path
import subprocess
import sys
def main():
    root = Path(__file__).resolve().parent
    for script in ['P3_analysis_upgrade.py', 'verify_sources_upgrade.py', 'build_manuscript_upgrade.py', 'check_upgrade.py', 'check_visual_upgrade.py']:
        print(f'Running {script}', flush=True)
        subprocess.run([sys.executable, str(root / script)], cwd=root, check=True)
if __name__ == '__main__':
    main()
