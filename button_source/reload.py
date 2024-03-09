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

from internals import reload

def run():
    reload.reload()
