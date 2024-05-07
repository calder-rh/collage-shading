from pymel.core import *

import importlib
from internals import network, global_controls, illuminee, reload, utilities
importlib.reload(network)
importlib.reload(global_controls)
importlib.reload(utilities)
importlib.reload(illuminee)
importlib.reload(reload)

from internals.illuminee import make_illuminee
from internals.global_controls import lighting_sets
from internals import reload


def run():
    lights = set(ls(lights=True))
    selection = ls(sl=True, transforms=True)
    selected_shapes = {item.getShape() for item in selection}
    selected_lights = lights & selected_shapes
    selected_illuminees = [make_illuminee(item) for item in selection if item.hasAttr('used_as_illuminee') and item.used_as_illuminee.get()]

    if selected_illuminees:
        for illuminee in selected_illuminees:
            illuminee.exclude_light(selected_lights)
    else:
        sets(lighting_sets.default_lights, remove=selected_lights)
    
    # reload.reload()
