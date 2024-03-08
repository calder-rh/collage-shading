from pymel.core import *

import importlib
from internals import measured_gradient, network, global_groups, global_controls, luminance, shadow_influences, utilities, illuminee
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(shadow_influences)
importlib.reload(utilities)
importlib.reload(illuminee)

from internals.illuminee import Illuminee

def run():
    selection = ls(sl=True)
    if not selection:
        return
    
    item = selection[0]
    Illuminee({'obj': item.name()}, item)
