from pymel.core import *

import importlib
from internals import measured_gradient, network, global_groups, global_controls, luminance, shadow_influences, invisible, illuminee
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(shadow_influences)
importlib.reload(invisible)
importlib.reload(illuminee)

from illuminee import Illuminee


def run():
    selection = ls(sl=True, transforms=True)
    selected_illuminees = [Illuminee(item) for item in selection if item.hasAttr('used_as_illuminee')]

    for illuminee in selected_illuminees:
        illuminee.connect_to_global()
