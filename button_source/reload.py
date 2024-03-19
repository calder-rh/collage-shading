from pymel.core import *

import importlib
from internals import network, global_controls, illuminee, reload, utilities
importlib.reload(network)
importlib.reload(global_controls)
importlib.reload(utilities)
importlib.reload(illuminee)
importlib.reload(reload)

from internals import reload

def run():
    reload.reload()
