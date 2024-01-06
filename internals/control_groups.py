from pymel.core import *
from internals.network import Network


class ControlGroups(Network):
    relevant_context = []
    prefix = ''
    delete = False
    
    def __init__(self, _):
        self.shading_controls = self.make(group, 'shading_controls', em=True)
        self.internals = self.make(group, 'internals', em=True)
        parent(self.internals, self.shading_controls)
        self.sun_pairs = self.make(group, 'sun_pairs', em=True)
        parent(self.sun_pairs, self.internals)
        self.lighting_groups = self.make(group, 'lighting_groups', em=True)
        parent(self.lighting_groups, self.internals)
