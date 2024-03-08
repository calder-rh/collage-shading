from pymel.core import *

import importlib
from internals import network, sun_pair, global_controls, global_groups, measured_gradient, luminance, shadow_influences, utilities, illuminee, screen_placement, tracking_projection, palettes, ground
importlib.reload(network)
importlib.reload(sun_pair)
importlib.reload(global_controls)
importlib.reload(global_groups)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(shadow_influences)
importlib.reload(utilities)
importlib.reload(illuminee)
importlib.reload(screen_placement)
importlib.reload(tracking_projection)
importlib.reload(palettes)
importlib.reload(atmospheric_perspective)
importlib.reload(ground)

from internals import ground

def run():
    selection = ls(sl=True)
    if selection:
        selected_obj = selection[0]
        if selected_obj.type() == 'transform':
            g = ground.Ground({'mesh': selected_obj.name()}, selected_obj)
            g.animate()
