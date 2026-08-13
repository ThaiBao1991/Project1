import subprocess
import sys
import importlib.util

def is_tool_installed(tool_name):
    return importlib.util.find_spec(tool_name) is not None

def install_tool(tool_name):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        return True
    except subprocess.CalledProcessError:
        return False
