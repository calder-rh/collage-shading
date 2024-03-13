from pymel.core import *

import importlib
from internals import measured_gradient, network, global_groups, global_controls, luminance, illuminee, utilities
importlib.reload(network)
importlib.reload(global_groups)
importlib.reload(global_controls)
importlib.reload(measured_gradient)
importlib.reload(luminance)
importlib.reload(utilities)
importlib.reload(illuminee)

from internals.illuminee import make_illuminee

def run():
    def selection_error():
        confirmDialog(t='Error', m='To add a proxy, select an illuminee and a proxy object. To remove a proxy, just select an illuminee.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()

    selection = ls(sl=True, transforms=True)
    if len(selection) not in [1, 2]:
        selection_error()
    
    illuminee_list = [item for item in selection if item.hasAttr('used_as_illuminee') and item.used_as_illuminee.get()]
    proxy_list = [item for item in selection if not (item.hasAttr('used_as_illuminee') and item.used_as_illuminee.get())]

    if not (len(illuminee_list) == 1 and len(proxy_list) <= 1):
        selection_error()

    illuminee_node = illuminee_list[0]
    illuminee = make_illuminee(illuminee_node)
    
    if proxy_list:
        proxy_meshes = listRelatives(proxy_list[0], ad=True, type='mesh')
        if not proxy_meshes:
            confirmDialog(t='Error', m='An empty transform node cannot be used as a proxy', b='OK', cb='OK', db='OK', icon='warning', ma='left')
            exit()
        illuminee.add_proxy(proxy_meshes)
    else:
        illuminee.remove_proxy()
