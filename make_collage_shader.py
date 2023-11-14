from pymel.core import *
import sys
from pathlib import Path
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network, shading_path, shading_controller, surface_values, coordinate_converter, palettes, collage_shader, world_placement, screen_placement, tracking_projection, dialog_with_support, make_collage_shader
importlib.reload(network)
importlib.reload(shading_path)
importlib.reload(shading_controller)
importlib.reload(surface_values)
importlib.reload(coordinate_converter)
importlib.reload(palettes)
importlib.reload(collage_shader)
importlib.reload(world_placement)
importlib.reload(screen_placement)
importlib.reload(tracking_projection)
importlib.reload(dialog_with_support)
importlib.reload(make_collage_shader)

from internals import make_collage_shader
make_collage_shader.run()