from pymel.core import *

import importlib
from internals import global_groups, network, sun_pair, global_controls
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(sun_pair)
importlib.reload(global_controls)

from internals.global_controls import global_controls

def run():
    selection = ls(sl=True)
    if not selection:
        global_controls.disconnect_camera()
    elif len(selection) == 1:
        node = selection[0]
        if node.type() == 'camera':
            cam = node.getTransform()
        elif node.type() == 'transform' and node.getShape().type() == 'camera':
            cam = node
        else:
            confirmDialog(t='Error', m='Please select a camera.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
            exit()
        global_controls.connect_camera(cam)
    else:
        confirmDialog(t='Error', m='Please select only one camera.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()
        
