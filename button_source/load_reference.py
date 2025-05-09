from pymel.core import *

import importlib
from internals import global_groups, network, sun_pair, global_controls, reload # TODO
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(sun_pair)
importlib.reload(global_controls)
importlib.reload(reload)

from internals.global_controls import gcn


def run():
    for referenced_gcn in ls('*::global_controls'):
        referenced_gcn.v.set(False)
        for attr_name in listAttr(gcn, ud=True):
            if referenced_gcn.hasAttr(attr_name):
                gcn.attr(attr_name) >> referenced_gcn.attr(attr_name)
    
    reload.reload()
