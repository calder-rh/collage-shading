from pymel.core import *
import sys
from importlib import reload
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

from internals.buttons import make_collage_shader
reload(make_collage_shader)
from internals.buttons import make_collage_shader
make_collage_shader.run()
