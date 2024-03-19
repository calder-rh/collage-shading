from pymel.core import *

import importlib
from internals import network, global_controls, illuminee, utilities
importlib.reload(network)
importlib.reload(global_controls)
importlib.reload(utilities)
importlib.reload(illuminee)

from internals.illuminee import make_illuminee


def run():
    selection = ls(sl=True, transforms=True)
    selected_illuminees = [make_illuminee(item) for item in selection if item.hasAttr('fantasy_shaded')]

    for illuminee in selected_illuminees:
        illuminee.connect_to_global()
