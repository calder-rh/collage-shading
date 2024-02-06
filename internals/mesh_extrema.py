from pymel.core import *
from internals.network import Network


class MeshExtrema(Network):
    relevant_context = ['mesh', 'sun_pair']

    def __init__(self, _, mesh, sun_position, antisun_position, direction_inverse_matrix):
        trans = mesh
        shape = trans.getShape()
        
        transform_geometry = self.utility('transformGeometry', 'transform_geometry')
        shape.worldMesh[0] >> transform_geometry.inputGeometry
        trans.worldMatrix[0] >> transform_geometry.transform

        light_point = self.utility('closestPointOnMesh', 'light_point')
        transform_geometry.outputGeometry >> light_point.inMesh
        sun_position >> light_point.inPosition

        dark_point = self.utility('closestPointOnMesh', 'dark_point')
        transform_geometry.outputGeometry >> dark_point.inMesh
        antisun_position >> dark_point.inPosition

        light_point_z_calculator = self.utility('pointMatrixMult', 'light_point_z_calculator')
        direction_inverse_matrix >> light_point_z_calculator.inMatrix
        light_point.position >> light_point_z_calculator.inPoint

        dark_point_z_calculator = self.utility('pointMatrixMult', 'dark_point_z_calculator')
        direction_inverse_matrix >> dark_point_z_calculator.inMatrix
        dark_point.position >> dark_point_z_calculator.inPoint

        self.light_z = light_point_z_calculator.outputZ
        self.dark_z = dark_point_z_calculator.outputZ


class MeasuredGradient(Network):
    relevant_context = ['obj', 'sun_pair']
    delete = True

    def __init__(self, context, meshes, sun_position, antisun_position, direction_inverse_matrix, surface_point_z):
        dark_z_calculator = self.utility('min', 'dark_z_calculator')
        light_z_calculator = self.utility('max', 'light_z_calculator')

        for i, mesh in enumerate(meshes):
            trans = mesh.getTransform()
            this_mesh_extrema = self.build(MeshExtrema({'mesh': trans.name(), 'sun_pair': context['sun_pair']}, trans, sun_position, antisun_position, direction_inverse_matrix), add_keys=False)
            this_mesh_extrema.light_z >> light_z_calculator.input[i]
            this_mesh_extrema.dark_z >> dark_z_calculator.input[i]
        
        gradient_calculator = self.utility('remapValue', 'gradient_calculator')
        dark_z_calculator.output >> gradient_calculator.inputMin
        light_z_calculator.output >> gradient_calculator.inputMax
        surface_point_z >> gradient_calculator.inputValue
        self.gradient_value = gradient_calculator.outValue
