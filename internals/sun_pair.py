from pymel.core import *
from internals.network import Network

from internals.global_groups import control_groups
from internals.invisible import set_visibility_in_render


class SunPairShaders(Network):
    relevant_context = []
    prefix = ''
    delete = False

    def __init__(self, _):
        sun_shader = self.shader('surfaceShader', 'sun_shader')
        sun_shader.outColor.set((1, 1, 1))
        self.sun_sg = self.utility('shadingEngine', 'sun_SG')
        sun_shader.outColor >> self.sun_sg.surfaceShader

        antisun_shader = self.shader('surfaceShader', 'antisun_shader')
        antisun_shader.outColor.set((0, 0, 0))
        self.antisun_sg = self.utility('shadingEngine', 'antisun_SG')
        antisun_shader.outColor >> self.antisun_sg.surfaceShader


class SunPair(Network):
    abbreviation = 'suns'
    relevant_context = ['usage']
    delete = False

    def __init__(self, _, rotation, sun_distance, make_objects=False):
        if make_objects:
            sun_group = self.make(group, 'sun_group', em=True)
            parent(sun_group, control_groups.sun_pairs)

            sun_trans_name = self.prefix + 'sun'
            sun_shape_name = self.prefix + 'sunShape'
            sun_platonic_name = self.prefix + 'sun_platonic'
            antisun_trans_name = self.prefix + 'antisun'
            antisun_shape_name = self.prefix + 'antisunShape'
            antisun_platonic_name = self.prefix + 'antisun_platonic'

            names = [sun_trans_name, sun_shape_name, sun_platonic_name, antisun_trans_name, antisun_shape_name, antisun_platonic_name]
            if all(objExists(name) for name in names):
                sun_trans = PyNode(sun_trans_name)
                sun_shape = PyNode(sun_shape_name)
                sun_platonic = PyNode(sun_platonic_name)
                antisun_trans = PyNode(antisun_trans_name)
                antisun_shape = PyNode(antisun_shape_name)
                antisun_platonic = PyNode(antisun_platonic_name)
            else:
                for name in names:
                    if objExists(name):
                        delete(name)

                shaders = SunPairShaders({})
                sun_trans, sun_platonic = polyPlatonic()
                sun_trans = PyNode(sun_trans)
                sun_trans.rename(sun_trans_name)
                sun_platonic = PyNode(sun_platonic)
                sun_platonic.rename(sun_platonic_name)
                sun_shape = sun_trans.getShape()
                sun_platonic.subdivisionMode.set(2)
                sun_platonic.subdivisions.set(1)
                sun_platonic.sphericalInflation.set(0)
                sun_trans.s.set((0.5, 0.5, 0.5))
                connection_counts = {}
                for edge in sun_shape.e:
                    for vertex in edge.connectedVertices():
                        index = vertex.index()
                        if index not in connection_counts:
                            connection_counts[index] = 0
                        connection_counts[index] += 1
                center_vertices = [index for index, count in connection_counts.items() if count == 3]
                select(clear=True)
                for index in center_vertices:
                    select(sun_shape.vtx[index], add=True)
                scale(3, 3, 3)
                select(clear=True)

                antisun_trans, antisun_platonic = polyPlatonic()
                antisun_trans = PyNode(antisun_trans)
                antisun_trans.rename(antisun_trans_name)
                antisun_platonic = PyNode(antisun_platonic)
                antisun_platonic.rename(antisun_platonic_name)
                antisun_shape = antisun_trans.getShape()
                antisun_platonic.sphericalInflation.set(1)
                displaySmoothness(antisun_shape, polygonObject=3)
                select(clear=True)

                initial_sg_connection = listConnections(sun_shape, s=False, c=True, p=True)[0]
                initial_sg_connection[0] // initial_sg_connection[1]
                initial_sg_connection = listConnections(antisun_shape, s=False, c=True, p=True)[0]
                initial_sg_connection[0] // initial_sg_connection[1]
                sets(shaders.sun_sg, e=True, fe=sun_shape)
                sets(shaders.antisun_sg, e=True, fe=antisun_shape)

                set_visibility_in_render(sun_shape, False)
                set_visibility_in_render(antisun_shape, False)

                parent(sun_trans, sun_group)
                parent(antisun_trans, sun_group)

                antisun_distance = self.multiply(sun_distance, -1, 'antisun_distance')

                sun_distance >> sun_trans.tz
                antisun_distance >> antisun_trans.tz

                rotation >> sun_group.r

            sun_decomposer = self.utility('decomposeMatrix', 'sun_decomposer')
            antisun_decomposer = self.utility('decomposeMatrix', 'antisun_decomposer')

            sun_trans.worldMatrix[0] >> sun_decomposer.inputMatrix
            self.sun_position = sun_decomposer.outputTranslate

            antisun_trans.worldMatrix[0] >> antisun_decomposer.inputMatrix
            self.antisun_position = antisun_decomposer.outputTranslate
        else:
            rotation_matrix = self.utility('composeMatrix', 'rotation_matrix')
            rotation >> rotation_matrix.inputRotate

            sun_matrix = self.utility('composeMatrix', 'sun_matrix')
            sun_distance >> sun_matrix.inputTranslateZ

            antisun_distance = self.multiply(sun_distance, -1, 'antisun_distance')
            antisun_matrix = self.utility('composeMatrix', 'antisun_matrix')
            antisun_distance >> antisun_matrix.inputTranslateZ

            sun_position_calculator = self.utility('multMatrix', 'sun_position_calculator')
            rotation_matrix.outputMatrix >> sun_position_calculator.matrixIn[1]
            sun_matrix.outputMatrix >> sun_position_calculator.matrixIn[0]

            antisun_position_calculator = self.utility('multMatrix', 'antisun_position_calculator')
            rotation_matrix.outputMatrix >> antisun_position_calculator.matrixIn[1]
            antisun_matrix.outputMatrix >> antisun_position_calculator.matrixIn[0]

            sun_decomposer = self.utility('decomposeMatrix', 'sun_decomposer')
            antisun_decomposer = self.utility('decomposeMatrix', 'antisun_decomposer')

            sun_position_calculator.matrixSum >> sun_decomposer.inputMatrix
            self.sun_position = sun_decomposer.outputTranslate

            antisun_position_calculator.matrixSum >> antisun_decomposer.inputMatrix
            self.antisun_position = antisun_decomposer.outputTranslate
        
        direction_matrix_composer = self.utility('composeMatrix', 'direction_matrix_composer')
        rotation >> direction_matrix_composer.inputRotate
        direction_matrix_inverter = self.utility('inverseMatrix', 'direction_matrix_inverter')
        direction_matrix_composer.outputMatrix >> direction_matrix_inverter.inputMatrix
        self.direction_inverse_matrix = direction_matrix_inverter.outputMatrix

        last_row_getter = self.utility('pointMatrixMult', 'last_row_getter')
        direction_matrix_composer.outputMatrix >> last_row_getter.inMatrix
        last_row_getter.inPoint.set((0, 0, 1))
        sampler_info = self.utility('samplerInfo', 'sampler_info')
        surface_dot = self.utility('aiDot', 'surface_dot')
        sampler_info.pointWorld >> surface_dot.input1
        last_row_getter.output >> surface_dot.input2
        self.surface_point_z = surface_dot.outValue