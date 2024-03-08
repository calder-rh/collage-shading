from pymel.core import *

import importlib
from internals import measured_gradient, network, global_groups, global_controls, luminance, shadow_influences, illuminee, reload, utilities
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(shadow_influences)
importlib.reload(utilities)
importlib.reload(illuminee)
importlib.reload(reload)

from illuminee import Illuminee
from global_groups import lighting_sets
from internals import reload


def run():
    lights = set(ls(lights=True))
    selection = ls(sl=True, transforms=True)
    selected_shapes = {item.getShape() for item in selection}
    selected_lights = lights & selected_shapes
    selected_illuminees = [Illuminee(item) for item in selection if item.hasAttr('used_as_illuminee') and item.used_as_illuminee.get()]

    if selected_illuminees:
        for illuminee in selected_illuminees:
            illuminee.exclude_light(selected_lights)
    else:
        sets(lighting_sets.default_lights, remove=selected_lights)
    
    reload.reload()
