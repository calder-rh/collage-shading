from pymel.core import *
import sys
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network, control_groups, shading_controller, sun_pair, invisible, lighting_controller, measured_gradient
importlib.reload(network)
importlib.reload(control_groups)
importlib.reload(invisible)
importlib.reload(sun_pair)
importlib.reload(shading_controller)
importlib.reload(lighting_controller)
importlib.reload(measured_gradient)

from internals.shading_controller import ShadingController
from internals.lighting_controller import LightingController
from internals.measured_gradient import MeasuredGradient


sc = ShadingController()
lc = LightingController({})

mg = MeasuredGradient({'meshes': 'test', 'sun_pair': 'light'}, [SCENE.pSphere1, SCENE.pSphere2], sc.suns.light_sun_position, sc.suns.light_antisun_position, sc.suns.light_direction_inverse_matrix, sc.suns.light_surface_point_z)
