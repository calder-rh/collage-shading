from pymel.core import *
from internals.network import Network


class MeasuredGradient(Network):
    relevant_context = ['obj', 'sun_pair']
    delete = True

    def __init__(self, context, mesh, sun_position, antisun_position, direction_inverse_matrix, surface_point_z):
        light_point = self.utility('closestPointOnMesh', 'light_point')
        mesh >> light_point.inMesh
        sun_position >> light_point.inPosition

        dark_point = self.utility('closestPointOnMesh', 'dark_point')
        mesh >> dark_point.inMesh
        antisun_position >> dark_point.inPosition

        light_point_z_calculator = self.utility('pointMatrixMult', 'light_point_z_calculator')
        direction_inverse_matrix >> light_point_z_calculator.inMatrix
        light_point.position >> light_point_z_calculator.inPoint

        dark_point_z_calculator = self.utility('pointMatrixMult', 'dark_point_z_calculator')
        direction_inverse_matrix >> dark_point_z_calculator.inMatrix
        dark_point.position >> dark_point_z_calculator.inPoint

        gradient_calculator = self.utility('remapValue', 'gradient_calculator')
        dark_point_z_calculator.outputZ >> gradient_calculator.inputMin
        light_point_z_calculator.outputZ >> gradient_calculator.inputMax
        surface_point_z >> gradient_calculator.inputValue
        self.gradient_value = gradient_calculator.outValue
