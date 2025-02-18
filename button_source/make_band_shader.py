from pymel.core import *

import importlib
from internals import (
    bands,
    network,
    global_controls,
    utilities,
    illuminee,
    screen_placement,
    tracking_projection,
    palettes,
)

importlib.reload(network)
importlib.reload(global_controls)
importlib.reload(utilities)
importlib.reload(illuminee)
importlib.reload(screen_placement)
importlib.reload(tracking_projection)
importlib.reload(palettes)
importlib.reload(bands)

from internals import bands


def run():
    selection = ls(sl=True)
    if selection:
        selected_obj = selection[0]
        if selected_obj.type() == "transform":
            g = bands.BandShader({"mesh": selected_obj.name()}, selected_obj)
            g.animate()
