from pymel.core import *
import sys, importlib
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

from button_source import add_light
importlib.reload(add_light)
from button_source import add_light
add_light.run()
