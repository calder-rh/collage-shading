from pymel.core import *
import sys
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network, sun_pair, global_controls, global_groups, measured_gradient, luminance, utilities, illuminee, screen_placement, tracking_projection, palettes, ground
importlib.reload(network)
importlib.reload(sun_pair)
importlib.reload(global_controls)
importlib.reload(global_groups)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(utilities)
importlib.reload(illuminee)
importlib.reload(screen_placement)
importlib.reload(tracking_projection)
importlib.reload(palettes)
importlib.reload(ground)

from internals import ground
g = ground.Ground({'mesh': 'test'}, PyNode('pPlane1'), '/Users/calder/Documents/Animation/Shading/shading/fantasy/palettes/3 grass/aigrass.jpg')
g.animate()