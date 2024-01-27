from pymel.core import *
from internals.network import Network


class Luminance(Network):
    relevant_context = []
    delete = False

    def __init__(self, _):
        luminance_node = self.utility('surfaceLuminance', 'surface_luminance')
        self.luminance = luminance_node.outValue


luminance_node = Luminance({})