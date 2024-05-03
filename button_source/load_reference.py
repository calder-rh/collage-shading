from pymel.core import *

import importlib
from internals import network, utilities, global_controls, reload # TODO
importlib.reload(network)
importlib.reload(utilities)
importlib.reload(global_controls)
importlib.reload(reload)

from internals.global_controls import gcn


# attrs_not_to_connect = [
#     'atmospheric_perspective',
#     'enable',
#     'min_distance',
#     'half_distance',
#     'ground_half_distance',
#     'color'
# ]

attrs_not_to_connect = []

def run():
    for referenced_gcn in ls('*::shading_controls'):
        referenced_gcn.v.set(False)
        for attr_name in listAttr(gcn, ud=True):
            if any(no in attr_name for no in attrs_not_to_connect):
                continue
            if referenced_gcn.hasAttr(attr_name):
                gcn.attr(attr_name) >> referenced_gcn.attr(attr_name)
    
    # reload.reload()
