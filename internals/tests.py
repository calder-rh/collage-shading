from pymel.core import *
import sys
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network, sun_pair, global_groups, global_controls, ground
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(sun_pair)
importlib.reload(global_controls)
importlib.reload(ground)

from internals import ground
xyz = ground.sy_to_uv(0.5, 0)
SCENE.marker.t.set(xyz)