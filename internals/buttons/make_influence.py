from pymel.core import *

import importlib
from internals import global_groups, network, sun_pair, global_controls
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(sun_pair)
importlib.reload(global_controls)

from global_controls import GlobalControls


def run():
    for mesh in ls(sl=True, dag=True, shapes=True):
        mesh.aiTraceSets.set(GlobalControls.shadow_trace_set)
        mesh.aiVisibleInDiffuseReflection.set(True)
