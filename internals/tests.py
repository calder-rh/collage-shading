from pymel.core import *
import sys
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network, sun_pair, control_groups
importlib.reload(network)
importlib.reload(sun_pair)
importlib.reload(control_groups)

from internals.sun_pair import SunPair

t = SunPair({'usage': 'test'}, SCENE.light_origin, SCENE.sun_distance.outFloat, make_objects=True)