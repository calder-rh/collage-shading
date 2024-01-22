from pymel.core import *
from internals.network import Network

from internals.control_groups import ControlGroups
import time


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
    relevant_context = ['meshes', 'sun_pair']

    def __init__(self, context, meshes, sun_position, antisun_position, direction_inverse_matrix, surface_point_z):
        dark_z_calculator = self.utility('min', 'dark_z_calculator')
        light_z_calculator = self.utility('max', 'light_z_calculator')

        timestamp_name = 'lg_' + str(time.time()).replace('.', '_')
        lighting_group = group(name=timestamp_name, em=True)
        addAttr(lighting_group, ln='members', multi=True)
        cg = ControlGroups({})
        parent(lighting_group, cg.illuminees)

        for i, mesh in enumerate(meshes):
            if mesh.type() == 'transform':
                trans = mesh
            else:
                trans = mesh.getTransform()
            mesh_ldzs = self.build(MeshExtrema({'mesh': trans.name(), 'sun_pair': context['sun_pair']}, trans, sun_position, antisun_position, direction_inverse_matrix), add_keys=False)
            mesh_ldzs.light_z >> light_z_calculator.input[i]
            mesh_ldzs.dark_z >> dark_z_calculator.input[i]

            if not hasAttr(mesh, 'lighting_group'):
                addAttr(mesh, ln='lighting_group')
            mesh.lighting_group >> lighting_group.members[i]
        
        gradient_calculator = self.utility('remapValue', 'gradient_calculator')
        dark_z_calculator.output >> gradient_calculator.inputMin
        light_z_calculator.output >> gradient_calculator.inputMax
        surface_point_z >> gradient_calculator.inputValue
        self.gradient_value = gradient_calculator.outValue
        
        