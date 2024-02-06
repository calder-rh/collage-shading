from pymel.core import *

import importlib
from internals import global_groups, network, sun_pair, global_controls
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(sun_pair)
importlib.reload(global_controls)


def run():
    ...
