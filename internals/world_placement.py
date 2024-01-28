from pymel.core import *
from internals.network import Network


class WorldPlacement(Network):
    relevant_context = ['mesh', 'facet']

    def __init__(self, context, obj, center_os, orienter_os):
        obj_matrix = obj.worldMatrix[0]

        obj_center_ws_calculator = self.utility('pointMatrixMult', 'obj_center_ws')
        obj_matrix >> obj_center_ws_calculator.inMatrix
        obj_center_ws_calculator.inPoint.set((0, 0, 0))
        self.obj_center_ws = obj_center_ws_calculator.output

        facet_center_ws_calculator = self.utility('pointMatrixMult', 'facet_center_ws')
        obj_matrix >> facet_center_ws_calculator.inMatrix
        facet_center_ws_calculator.inPoint.set(center_os)
        self.facet_center_ws = facet_center_ws_calculator.output

        rotation_ws_calculator = self.utility('pointMatrixMult', 'rotation_ws')
        obj_matrix >> rotation_ws_calculator.inMatrix
        rotation_ws_calculator.inPoint.set(orienter_os)
        self.rotation_ws = rotation_ws_calculator.output
