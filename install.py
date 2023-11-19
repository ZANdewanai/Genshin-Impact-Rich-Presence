import subprocess
import sys
import importlib

if __name__ == "__main__":
    try:
        print("Checking for required dependencies")
        importlib.import_module("main")
    except ImportError:
        print("Not found. Installing required modules")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "torch",
                    "torchvision",
                    "--index-url",
                    "https://download.pytorch.org/whl/cu118",
                ]
            )
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            )
            print("Successfully installed module dependencies")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install module dependencies: {e}")
