#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run(cmd, cwd=None, capture=True):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True)
    if capture:
        print(result.stdout)
        if result.stderr:
            print("ERR:", result.stderr, file=sys.stderr)
    else:
        result.check_returncode()
    return result

def check_docker():
    try:
        run(["docker", "--version"])
        run(["docker", "ps"])
        return True
    except Exception as e:
        print(f"Docker check failed: {e}")
        return False

def start_docker():
    print("Attempting to start Docker daemon...")
    try:
        run(["sudo", "systemctl", "start", "docker"])
        run(["docker", "ps"])
        return True
    except Exception as e:
        print(f"Failed to start Docker: {e}")
        return False

def clone_repo(install_dir):
    repo_url = "https://github.com/Septa-Serpenta-Seraph/AEGIS-Dashboard"
    if not install_dir.exists():
        install_dir.mkdir(parents=True)
        run(["git", "clone", repo_url, str(install_dir)])
    else:
        run(["git", "-C", str(install_dir), "pull"])
    return install_dir

def install_requirements(install_dir):
    req_file = install_dir / "requirements.txt"
    if req_file.exists():
        run([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
    else:
        print("No requirements.txt found; skipping Python deps")

def create_env(install_dir):
    env_example = install_dir / ".env.example"
    env_file = install_dir / ".env"
    if env_example.exists() and not env_file.exists():
        env_content = env_example.read_text()
        env_file.write_text(env_content)
        print(f"Created .env at {env_file} (please edit with real values)")

def run_dashboard(install_dir):
    print("Starting AEGIS Dashboard... (Ctrl-C to stop)")
    run([sys.executable, "app.py"], cwd=install_dir, capture=False)

def main():
    install_dir = Path("/opt/AEGIS-Dashboard")
    print(f"Target directory: {install_dir}")
    
    if not check_docker():
        print("Docker is not active. Attempting to start...")
        if not start_docker():
            print("ERROR: Docker is required but could not be started.")
            print("Please start Docker manually: sudo systemctl start docker")
            sys.exit(1)
    
    print("Cloning/updating AEGIS Dashboard...")
    clone_repo(install_dir)
    
    print("Installing Python dependencies...")
    install_requirements(install_dir)
    
    print("Setting up environment file...")
    create_env(install_dir)
    
    print("
Setup complete! To run the dashboard:")
    print(f"  cd {install_dir}")
    print("  python app.py")
    print("
Or use this skill with --run to launch now.")
    
    if "--run" in sys.argv:
        run_dashboard(install_dir)

if __name__ == "__main__":
    main()
