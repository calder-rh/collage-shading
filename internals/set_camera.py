from pymel.core import *

from internals.shading_controller import ShadingController


def run():
    selection = ls(sl=True)
    if not selection:
        sc = ShadingController()
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
        sc = ShadingController()
        sc.connect_camera(cam)
    else:
        confirmDialog(t='Error', m='Please select only one camera.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()
