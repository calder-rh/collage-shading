from pymel.core import *

import importlib
from internals import network, global_groups, global_controls, mesh_extrema, luminance, shadow_influences, invisible, illuminee
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(mesh_extrema)
importlib.reload(luminance)
importlib.reload(shadow_influences)
importlib.reload(invisible)
importlib.reload(illuminee)

from internals.illuminee import Illuminee

def run():
    def selection_error():
        confirmDialog(t='Error', m='To add a proxy, select an illuminee and the proxy object. To remove a proxy, just select an illuminee.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()

    selection = ls(sl=True)
    if len(selection) not in [1, 2]:
        selection_error()
    illuminee_list = [item for item in selection if item.type() == 'transform' and item.hasAttr('used_as_illuminee')]
    proxy_list = [item for item in selection if item.type() in ['transform', 'mesh'] and not item.hasAttr('used_as_illuminee')]
    if not (len(illuminee_list) == 1 and len(proxy_list) <= 1):
        selection_error()

    illuminee_node = illuminee_list[0]
    illuminee = Illuminee({'obj': illuminee_node.name()})
    
    if proxy_list:
        proxy_node = proxy_list[0]
        if proxy_node.type() == 'transform':
            if (shape := proxy_node.getShape()):
                proxy_node = shape
            else:
                confirmDialog(t='Error', m='A proxy must be a single mesh.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
                exit()
        illuminee.add_proxy(shape)
    else:
        illuminee.remove_proxy()
