from pymel.core import *
from internals.network import Network


class ControlGroups(Network):
    relevant_context = []
    prefix = ''
    delete = False
    
    def __init__(self, _):
        self.controls = self.make(group, 'collage_shading', em=True)
        self.internals = self.make(group, 'internals', em=True)
        parent(self.internals, self.controls)
        self.sun_pairs = self.make(group, 'sun_pairs', em=True)
        parent(self.sun_pairs, self.internals)
        self.illuminees = self.make(group, 'illuminees', em=True)
        parent(self.illuminees, self.internals)

control_groups = ControlGroups({})