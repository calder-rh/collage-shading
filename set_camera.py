from pymel.core import *

import sys
from pathlib import Path
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network, shading_controller
importlib.reload(network)
importlib.reload(shading_controller)
from internals import network

from internals.shading_controller import ShadingController


sc = ShadingController({})

selection = ls(sl=True)
if not selection:
    sc.disconnect_camera()
elif len(selection) == 1:
    node = selection[0]
    if node.type() == 'camera':
        cam = node.getTransform()
    elif node.type() == 'transform' and node.getShape().type() == 'camera':
        cam = node
    else:
        confirmDialog(t='Error', m='Please select a camera.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()
    sc.connect_camera(cam)
else:
    confirmDialog(t='Error', m='Please select only one camera.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
    exit()
