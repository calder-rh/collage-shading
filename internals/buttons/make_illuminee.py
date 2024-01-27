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

from internals.illuminee import Illuminee

def run():
    selection = ls(sl=True)
    if not selection:
        return
    
    item = selection[0]
    Illuminee({'obj': item.name()}, item)
