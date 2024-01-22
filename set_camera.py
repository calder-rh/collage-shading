from pymel.core import *
import sys
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

selection = ls(sl=True)

import importlib
from internals import network, control_groups, sun_pair, global_controls, set_camera
importlib.reload(network)
importlib.reload(control_groups)
importlib.reload(sun_pair)
importlib.reload(global_controls)
importlib.reload(set_camera)

select(selection, replace=True)

from internals import set_camera
set_camera.run()