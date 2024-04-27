from pymel.core import *
import sys
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

from importlib import reload
from internals import shading_path
reload(shading_path)
from internals import shading_path

print(shading_path.relative_path_string('/Users/calder/Documents/Animation/Shading/shading/fantasy/palettes/4 bird/7 pastel red light/s2 pastel red light.psd'))