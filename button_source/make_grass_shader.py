from pymel.core import *

import importlib
from internals import network, utilities, grass_shader

importlib.reload(network)
importlib.reload(utilities)
importlib.reload(grass_shader)

from internals.grass_shader import GrassShader


def run():
    o = ls(sl=True)[0]
    GrassShader(
        {"mesh": "test"},
        o,
        "/Volumes/2023/shading/fantasy/palettes/2 terrain/4 new grass",
    )
