from pymel.core import *
from internals.network import Network


class ControlGroups(Network):
    relevant_context = []
    prefix = ''
    delete = False
    
    def __init__(self, _):
        self.controls = self.make(group, 'collage_shading', em=True)

        self.internals = self.make(group, 'internals', em=True)
        self.sun_pairs = self.make(group, 'sun_pairs', em=True)
        self.illuminees = self.make(group, 'illuminees', em=True)

        parent(self.internals, self.controls)
        parent(self.sun_pairs, self.internals)
        parent(self.illuminees, self.internals)

control_groups = ControlGroups({})


class LightingSets(Network):
    relevant_context = []
    prefix = ''
    delete = False

    def __init__(self, _):
        self.global_set = sets(name='lighting_sets', em=True)

        self.mesh_groups = sets(name='mesh_groups')
        self.default_lights = sets(name='default_lights')
        self.added_lights_sets = sets(name='added_lights_sets')
        self.excluded_lights_sets = sets(name='excluded_lights_sets')

        sets(self.global_set, add=self.mesh_groups)
        sets(self.global_set, add=self.default_lights)
        sets(self.global_set, add=self.added_lights_sets)
        sets(self.global_set, add=self.excluded_lights_sets)
    
    def add_light(self, light):
        sets(self.default_lights, add=light)
    
    def remove_light(self, light):
        sets(self.default_lights, remove=light)

lighting_sets = LightingSets({})