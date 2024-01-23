from pymel.core import *
from internals.network import Network
from internals.control_groups import control_groups
from internals.global_controls import gcn


class Illuminee(Network):
    relevant_context = ['id']
    
    global_set_name = 'illuminee_sets'
    mesh_sets_name = 'meshes'
    meshes_partition_name = 'illuminee_meshes_partition'
    add_lights_sets_name = 'add_lights'
    exclude_lights_sets_name = 'exclude_lights'

    def __init__(self, context):
        # is_new = not objExists(self.node_name)
        is_new = True # TODO

        if is_new:
            if not objExists(Illuminee.global_set_name):
                self.global_set = sets(name=Illuminee.global_set_name, em=True)
                self.mesh_sets = sets(name=Illuminee.mesh_sets_name, em=True)
                sets(self.global_set, add=self.mesh_sets)
                self.add_lights_sets = sets(name=Illuminee.add_lights_sets_name, em=True)
                sets(self.global_set, add=self.add_lights_sets)
                self.exclude_lights_sets = sets(name=Illuminee.exclude_lights_sets_name, em=True)
                sets(self.global_set, add=self.exclude_lights_sets)
            else:
                self.global_set = PyNode(Illuminee.global_set_name)
                self.meshes = PyNode(Illuminee.mesh_sets_name)
                self.add_lights_sets = PyNode(Illuminee.add_lights_sets_name)
                self.exclude_lights_sets = PyNode(Illuminee.exclude_lights_sets_name)

            self.mesh_set = self.make(sets, 'meshes', em=True)
            if not objExists(Illuminee.meshes_partition_name):
                partition(name=Illuminee.meshes_partition_name)
            
            sets(self.mesh_sets, add=self.mesh_set)
            partition(self.mesh_set, add=Illuminee.meshes_partition_name)

            self.add_lights_set = self.make(sets, 'add_lights', em=True)
            sets(self.add_lights_sets, add=self.add_lights_set)

            self.exclude_lights_set = self.make(sets, 'exclude_lights', em=True)
            sets(self.exclude_lights_sets, add=self.exclude_lights_set)

            self.control_node = self.make(group, 'illuminee', em=True)
            parent(self.control_node, control_groups.illuminees)

            # addAttr(self.control_node, ln='internals', at='compound', nc=)

            addAttr(self.control_node, ln='meshes', at='message')
            self.mesh_set.message >> self.control_node.meshes
            addAttr(self.control_node, ln='add_lights', at='message')
            self.add_lights_set.message >> self.control_node.add_lights
            addAttr(self.control_node, ln='exclude_lights', at='message')
            self.exclude_lights_set.message >> self.control_node.exclude_lights

            addAttr(self.control_node, ln='proxy_object', at='message')

            # addAttr(self.control_node)

    def add_mesh(self, mesh):
        ...
    
    def remove_mesh(self, mesh):
        ...
    
    def add_proxy(self, mesh):
        ...
    
    def remove_proxy(self, mesh):
        ...
    
    def include_light(self, mesh):
        ...
    
    def exclude_light(self, mesh):
        ...
    
    def reconnect_to_gcn(self):
        ...

    