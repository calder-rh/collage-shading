from pymel.core import *

import importlib
from internals import network, grass_shader

importlib.reload(network)
importlib.reload(grass_shader)

from internals.grass_shader import GrassShader


def run():
    o = ls(sl=True)[0]
    GrassShader({"mesh": "test"}, o, None)
