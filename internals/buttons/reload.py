from pymel.core import *

import importlib
from internals import network, global_groups, global_controls, mesh_extrema, luminance, shadow_influences, invisible, illuminee
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(mesh_extrema)
importlib.reload(luminance)
importlib.reload(shadow_influences)
importlib.reload(invisible)
importlib.reload(illuminee)

from internals.global_groups import lighting_sets
from internals.illuminee import Illuminee

def run():
    for group in sets(lighting_sets.mesh_groups, q=1):
        illuminee = Illuminee({group.name()}, group)
        illuminee.reload_meshes()
        illuminee.link_lights()
