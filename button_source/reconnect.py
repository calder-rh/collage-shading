from pymel.core import *

import importlib
from internals import measured_gradient, network, global_groups, global_controls, luminance, illuminee, utilities
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(utilities)
importlib.reload(illuminee)

from internals.illuminee import make_illuminee


def run():
    selection = ls(sl=True, transforms=True)
    selected_illuminees = [make_illuminee(item) for item in selection if item.hasAttr('used_as_illuminee')]

    for illuminee in selected_illuminees:
        illuminee.connect_to_global()
