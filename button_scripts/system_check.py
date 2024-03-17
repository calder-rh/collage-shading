from pymel.core import *
import sys, importlib
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

try:
    from button_source import system_check
    importlib.reload(system_check)
    from button_source import system_check
    system_check.run()
except ModuleNotFoundError:
    system_check.error('Make sure to set your project to the 2023 folder on the CS filesystem')
