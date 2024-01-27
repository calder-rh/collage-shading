from pymel.core import *
from internals.network import Network
from internals.global_controls import gcn


trace_set_name = 'distance_from_influence'


class ShadowDistance(Network):
    relevant_context = []
    delete = False

    def __init__(self, _):
        distance_node = self.utility('aiDistance', trace_set_name)
        distance_node.traceSet.set('shadow_influences')
        gcn.shadow_influences_distance >> distance_node.distance
        distance_remap = self.utility('remapValue', 'remap_distance')
        distance_remap.outputMin.set(-1)
        distance_remap.outputMax.set(0)
        distance_node.outColorR >> distance_remap.inputValue
        self.shadow_distance = distance_remap.outValue

shadow_distance_node = ShadowDistance({})


def make_shadow_influence():
    for mesh in ls(sl=True, dag=True, shapes=True):
        mesh.aiTraceSets.set(trace_set_name)

def remove_shadow_influence():
    for mesh in ls(sl=True, dag=True, shapes=True):
        mesh.aiTraceSets.set('')
