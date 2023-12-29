from pymel.core import *
import sys
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network, control_groups, shading_controller, sun_pair, invisible, lighting_controller
importlib.reload(network)
importlib.reload(control_groups)
importlib.reload(invisible)
importlib.reload(sun_pair)
importlib.reload(shading_controller)
importlib.reload(lighting_controller)

from internals.lighting_controller import LightingController

t = LightingController({})