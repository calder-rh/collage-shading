from pymel.core import *

import importlib
from internals import measured_gradient, network, global_groups, global_controls, luminance, illuminee, reload, utilities
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(utilities)
importlib.reload(illuminee)
importlib.reload(reload)

from internals.illuminee import make_illuminee
from internals import reload


def run():
    lights = set(ls(lights=True))
    selection = ls(sl=True, transforms=True)
    selected_shapes = {item.getShape() for item in selection}
    selected_lights = lights & selected_shapes
    selected_illuminee_nodes = [item for item in selection if item.hasAttr('used_as_illuminee') and item.used_as_illuminee.get()]

    if selected_illuminee_nodes:
        illuminee_nodes = selected_illuminee_nodes
    else:
        illuminee_nodes = set().union(*[set(sets(set_node, q=True)) for set_node in ls('::illuminees', sets=True)])
    
    illuminees = [make_illuminee(node) for node in illuminee_nodes]

    if selected_lights:
        for illuminee in illuminees:
            illuminee.reset_light(selected_lights)
    else:
        for illuminee in illuminees:
            illuminee.reset_lights()

    reload.reload()
