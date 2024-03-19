from pymel.core import *

import importlib
from internals import network, global_controls, utilities, illuminee
importlib.reload(network)
importlib.reload(global_controls)
importlib.reload(utilities)
importlib.reload(illuminee)

from internals.illuminee import Illuminee

def run():
    selection = ls(sl=True)
    if not selection:
        return
    
    item = selection[0]
    Illuminee({'obj': item.name()}, item)
