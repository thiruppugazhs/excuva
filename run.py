import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(base_dir, '.venv', 'Scripts', 'python.exe')
    
    if not os.path.exists(venv_python):
        venv_python = sys.executable

    app_path = os.path.join(base_dir, 'app.py')
    print("==========================================================")
    print("  EXCUSE.AI — AI-Powered Intelligent Excuse Generator")
    print("  Running on: http://127.0.0.1:5000")
    print("==========================================================")
    
    cmd = [venv_python, app_path]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == '__main__':
    main()
