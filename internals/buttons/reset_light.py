from pymel.core import *

import importlib
from internals import measured_gradient, network, global_groups, global_controls, luminance, shadow_influences, invisible, illuminee, reload
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(shadow_influences)
importlib.reload(invisible)
importlib.reload(illuminee)
importlib.reload(reload)

from illuminee import Illuminee
from internals import reload


def run():
    lights = set(ls(lights=True))
    selection = ls(sl=True, transforms=True)
    selected_shapes = {item.getShape() for item in selection}
    selected_lights = lights & selected_shapes
    selected_illuminees = [Illuminee(item) for item in selection if item.hasAttr('used_as_illuminee')]

    if selected_illuminees:
        illuminees = selected_illuminees
    else:
        illuminees = set(sets(ls('::illuminees', sets=True), union=True))

    if selected_lights:
        for illuminee in illuminees:
            illuminee.reset_light(selected_lights)
    else:
        for illuminee in illuminees:
            illuminee.reset_lights()

    reload.reload()
