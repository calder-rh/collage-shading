from pymel.core import *
from internals.network import Network

from internals.utilities import set_visibility_in_render
from internals.sun_pair import SunPairShaders, SunPair
from internals.global_groups import control_groups


class GlobalControls(Network):
    relevant_context = []
    prefix = ''
    delete = False

    node_name = 'global_controls'
    shadow_trace_set = 'shadow_influences'

    def __init__(self, _):
        is_new = not objExists(self.node_name)

        if is_new:
            lighting_controller_trans, _ = self.poly(polyCube, self.node_name, w=20, h=20, d=20)
            setAttr(lighting_controller_trans.r, l=True)
            lighting_controller_shape = lighting_controller_trans.getShape()
            set_visibility_in_render(lighting_controller_shape, False)
            parent(lighting_controller_trans, control_groups.controls)
            delete(lighting_controller_trans, ch=True)

            light_direction_cone_trans, _ = self.poly(polyCone, 'light_direction_cone', radius=8, height=80, heightBaseline=-1, axis=(0, 0, 1))
            light_source_ball_trans, _ = self.poly(polySphere, 'light_source_ball', radius=4, axis=(0, 0, 1))
            light_source_ball_trans.tz.set(78)
            self.light_direction_trans, _ = polyUnite(light_direction_cone_trans, light_source_ball_trans, n='light_direction')
            light_direction_shape = self.light_direction_trans.getShape()
            delete(self.light_direction_trans, ch=True)

            initial_sg_connection = listConnections(light_direction_shape, s=False, c=True, p=True)[0]
            initial_sg_connection[0] // initial_sg_connection[1]
            sun_sg = SunPairShaders({}).sun_sg
            sets(sun_sg, e=True, fe=light_direction_shape)
            parent(self.light_direction_trans, lighting_controller_trans)
            setAttr(self.light_direction_trans.t, l=True)
            setAttr(self.light_direction_trans.s, l=True)
            set_visibility_in_render(light_direction_shape, False)

            gcn = lighting_controller_trans
            addAttr(gcn, ln='gradients_weight', min=0, smx=1, dv=1)
            addAttr(gcn, ln='angle_weight', min=0, smx=1, dv=0)
            addAttr(gcn, ln='lights_weight', min=0, smx=1, dv=1)
            addAttr(gcn, ln='shadow_influences_weight', min=0, smx=1, dv=0.5)

            addAttr(gcn, ln='shadow_influences_distance', min=0, smx=1, dv=1)

            addAttr(gcn, ln='min_value', min=0, max=1, dv=0)
            addAttr(gcn, ln='max_value', min=0, max=1, dv=1)

            addAttr(gcn, ln='min_saturation', min=0, max=1, dv=0.5)
            addAttr(gcn, ln='saturation_falloff_point', min=0, max=1, dv=0.5)

            addAttr(gcn, ln='noise_frequency', min=1, smx=2000, dv=2000)
            addAttr(gcn, ln='noise_strength', min=0, max=1, dv=0.1)

            addAttr(gcn, ln='default_lightness', min=0, max=1, dv=0.5)

            addAttr(gcn, ln='ground_y', smn=-10, smx=10, dv=0, k=True)

            addAttr(gcn, ln='sun_distance', min=0, smx=100000, dv=10000)

            addAttr(gcn, ln='texture_scale', min=0, smx=100, dv=10)
            
            addAttr(gcn, ln='atmospheric_perspective', at='compound', nc=5)
            addAttr(gcn, p='atmospheric_perspective', ln='enable', at='bool')
            addAttr(gcn, p='atmospheric_perspective', ln='min_distance', min=0, smx=1000, dv=100)
            addAttr(gcn, p='atmospheric_perspective', ln='half_distance', min=1, smx=10000, dv=1000)
            addAttr(gcn, p='atmospheric_perspective', ln='color', at='float3', uac=True)
            addAttr(gcn, ln='colorR', at='float', parent='color')
            addAttr(gcn, ln='colorG', at='float', parent='color')
            addAttr(gcn, ln='colorB', at='float', parent='color')
            addAttr(gcn, p='atmospheric_perspective', ln='enhance_saturation', min=1, max=5, dv=2)
            lighting_controller_trans.atmospheric_perspective.color.set(0.5, 0.7, 1)

            addAttr(gcn, ln='ground', at='compound', nc=3)
            addAttr(gcn, p='ground', ln='band_spacing', dv=200)
            addAttr(gcn, p='ground', ln='band_count', at='short', dv=20)
            addAttr(gcn, p='ground', ln='initial_band_offset', dv=0)

            addAttr(gcn, ln='camera', at='compound', nc=7)
            addAttr(gcn, p='camera', ln='camera_message', at='message')
            addAttr(gcn, p='camera', ln='world_matrix', at='matrix')
            addAttr(gcn, p='camera', ln='inverse_world_matrix', at='matrix')
            addAttr(gcn, p='camera', ln='focal_length', dv=35)
            addAttr(gcn, p='camera', ln='horizontal_aperture', dv=1.417)
            addAttr(gcn, p='camera', ln='aspect_ratio')
            addAttr(gcn, p='camera', ln='focal_length_factor')

            addAttr(gcn, ln='suns', at='compound', nc=8)
            addAttr(gcn, p='suns', ln='light_sun_position', at='float3')
            addAttr(gcn, ln='light_sun_position_x', at='float', p='light_sun_position')
            addAttr(gcn, ln='light_sun_position_y', at='float', p='light_sun_position')
            addAttr(gcn, ln='light_sun_position_z', at='float', p='light_sun_position')
            addAttr(gcn, p='suns', ln='light_antisun_position', at='float3')
            addAttr(gcn, ln='light_antisun_position_x', at='float', p='light_antisun_position')
            addAttr(gcn, ln='light_antisun_position_y', at='float', p='light_antisun_position')
            addAttr(gcn, ln='light_antisun_position_z', at='float', p='light_antisun_position')
            addAttr(gcn, ln='light_direction_inverse_matrix', at='matrix', p='suns')
            addAttr(gcn, ln='light_surface_point_z', p='suns')
            addAttr(gcn, p='suns', ln='camera_sun_position', at='float3')
            addAttr(gcn, ln='camera_sun_position_x', at='float', p='camera_sun_position')
            addAttr(gcn, ln='camera_sun_position_y', at='float', p='camera_sun_position')
            addAttr(gcn, ln='camera_sun_position_z', at='float', p='camera_sun_position')
            addAttr(gcn, p='suns', ln='camera_antisun_position', at='float3')
            addAttr(gcn, ln='camera_antisun_position_x', at='float', p='camera_antisun_position')
            addAttr(gcn, ln='camera_antisun_position_y', at='float', p='camera_antisun_position')
            addAttr(gcn, ln='camera_antisun_position_z', at='float', p='camera_antisun_position')
            addAttr(gcn, ln='camera_direction_inverse_matrix', at='matrix', p='suns')
            addAttr(gcn, ln='camera_surface_point_z', p='suns')

            addAttr(gcn, ln='other_internals', at='compound', nc=8)
            addAttr(gcn, p='other_internals', ln='noise')
            addAttr(gcn, p='other_internals', ln='shadow_influences')
            addAttr(gcn, p='other_internals', ln='ground_mesh', dt='mesh')
            addAttr(gcn, p='other_internals', ln='band_offset')
            addAttr(gcn, p='other_internals', ln='atmospheric_perspective_amount')
            addAttr(gcn, p='other_internals', ln='camera_direction_vector', at='float3')
            addAttr(gcn, ln='camera_direction_vector_x', at='float', p='camera_direction_vector')
            addAttr(gcn, ln='camera_direction_vector_y', at='float', p='camera_direction_vector')
            addAttr(gcn, ln='camera_direction_vector_z', at='float', p='camera_direction_vector')
            addAttr(gcn, p='other_internals', ln='light_direction_vector', at='float3')
            addAttr(gcn, ln='light_direction_vector_x', at='float', p='light_direction_vector')
            addAttr(gcn, ln='light_direction_vector_y', at='float', p='light_direction_vector')
            addAttr(gcn, ln='light_direction_vector_z', at='float', p='light_direction_vector')
            addAttr(gcn, ln='light_dot', at='float', p='other_internals')



            # Make the sun pairs

            light_sun_pair = SunPair({'usage': 'light'}, self.light_direction_trans.r, gcn.sun_distance, make_objects=True)
            camera_decomposer = self.utility('decomposeMatrix', 'camera_decomposer')
            gcn.camera.world_matrix >> camera_decomposer.inputMatrix
            camera_sun_pair = SunPair({'usage': 'camera'}, camera_decomposer.outputRotate, gcn.sun_distance)

            light_sun_pair.sun_position >> gcn.suns.light_sun_position
            light_sun_pair.antisun_position >> gcn.suns.light_antisun_position
            light_sun_pair.direction_inverse_matrix >> gcn.suns.light_direction_inverse_matrix
            light_sun_pair.surface_point_z >> gcn.suns.light_surface_point_z
            camera_sun_pair.sun_position >> gcn.suns.camera_sun_position
            camera_sun_pair.antisun_position >> gcn.suns.camera_antisun_position
            camera_sun_pair.direction_inverse_matrix >> gcn.suns.camera_direction_inverse_matrix
            camera_sun_pair.surface_point_z >> gcn.suns.camera_surface_point_z


            # Calculate the camera and light direction vectors

            camera_rotation_matrix = self.utility('composeMatrix', 'camera_rotation_matrix')
            camera_decomposer.outputRotate >> camera_rotation_matrix.inputRotate
            move_1_z = self.utility('composeMatrix', 'move_1_z')
            move_1_z.inputTranslateZ.set(1)
            move_1_in_camera_direction = self.utility('multMatrix', 'move_1_in_camera_direction')
            move_1_z.outputMatrix >> move_1_in_camera_direction.matrixIn[0]
            camera_rotation_matrix.outputMatrix >> move_1_in_camera_direction.matrixIn[1]
            camera_rotation_calculator = self.utility('decomposeMatrix', 'camera_rotation_calculator')
            move_1_in_camera_direction.matrixSum >> camera_rotation_calculator.inputMatrix
            camera_rotation_calculator.outputTranslate >> gcn.other_internals.camera_direction_vector

            decompose_light = self.utility('decomposeMatrix', 'decompose_light')
            self.light_direction_trans.worldMatrix[0] >> decompose_light.inputMatrix
            light_rotation_matrix = self.utility('composeMatrix', 'light_rotation_matrix')
            decompose_light.outputRotate >> light_rotation_matrix.inputRotate
            move_1_z = self.utility('composeMatrix', 'move_1_z')
            move_1_z.inputTranslateZ.set(1)
            move_1_in_light_direction = self.utility('multMatrix', 'move_1_in_light_direction')
            move_1_z.outputMatrix >> move_1_in_light_direction.matrixIn[0]
            light_rotation_matrix.outputMatrix >> move_1_in_light_direction.matrixIn[1]
            light_rotation_calculator = self.utility('decomposeMatrix', 'light_rotation_calculator')
            move_1_in_light_direction.matrixSum >> light_rotation_calculator.inputMatrix
            light_rotation_calculator.outputTranslate >> gcn.other_internals.light_direction_vector


            global_sampler_info = self.utility('samplerInfo', 'global_sampler_info')


            # Calculate the global surface normal and dot with light direction

            transposed_camera = self.utility('transposeMatrix', 'transposed_camera')
            camera_rotation_matrix.outputMatrix >> transposed_camera.inputMatrix
            normal_components = []
            for i in range(3):
                row = self.utility('pointMatrixMult', f'camera_row_{i + 1}')
                transposed_camera.outputMatrix >> row.inMatrix
                vector = [0, 0, 0]
                vector[i] = 1
                row.inPoint.set(vector)
                component = self.utility('aiDot', f'normal_component_{i + 1}')
                row.output >> component.input1
                global_sampler_info.normalCamera >> component.input2
                normal_components.append(component)
            light_dot = self.utility('aiDot', 'light_dot')
            gcn.other_internals.light_direction_vector >> light_dot.input1
            for component, attr_axis in zip(normal_components, 'XYZ'):
                component.outValue >> light_dot.attr('input2' + attr_axis)
            light_dot.outValue >> gcn.other_internals.light_dot



            # Calculate the aspect ratio

            res = SCENE.defaultResolution
            aspect_ratio = self.divide(res.width, res.height, 'aspect_ratio')
            aspect_ratio >> gcn.aspect_ratio


            # Calculate the focal length factor

            millimeters_per_inch = 25.4
            attrs = ['focal_length',
                    'horizontal_aperture',
                    'focal_length_factor']
            expr = f'focal_length_factor = focal_length / (horizontal_aperture * {millimeters_per_inch});'
            node = self.expression('focal_length_factor', attrs, expr)
            gcn.camera.horizontal_aperture >> node.horizontal_aperture
            gcn.camera.focal_length >> node.focal_length        
            node.focal_length_factor >> gcn.focal_length_factor


            # Calculate the global noise

            noise = self.utility('aiNoise', 'value_noise')
            noise.coordSpace.set(3)
            gcn.noise_frequency >> noise.scale.scaleX
            gcn.noise_frequency >> noise.scale.scaleY
            gcn.noise_frequency >> noise.scale.scaleZ

            noise_projection = self.utility('projection', 'noise_projection')
            noise_projection.projType.set(8)
            gcn.camera.camera_message >> noise_projection.linkedCamera
            noise.outColor >> noise_projection.image

            noise_remap = self.utility('remapValue', 'noise_remap')
            noise_projection.outColor.outColorR >> noise_remap.inputValue
            noise_min = self.multiply(gcn.noise_strength, -1, 'noise_min')
            noise_min >> noise_remap.outputMin
            gcn.noise_strength >> noise_remap.outputMax
            
            noise_remap.outValue >> gcn.noise


            # Calculate the shadow influences

            distance_node = self.utility('aiDistance', 'distance_from_influence')
            distance_node.traceSet.set(GlobalControls.shadow_trace_set)
            gcn.shadow_influences_distance >> distance_node.distance
            distance_remap = self.utility('remapValue', 'remap_distance')
            distance_remap.outputMin.set(-1)
            distance_remap.outputMax.set(0)
            distance_node.outColorR >> distance_remap.inputValue
            gcn.shadow_influence = distance_remap.outValue


            # Calculate the atmospheric perspective amount

            dx = self.subtract(camera_decomposer.outputTranslateX, global_sampler_info.pointWorldX, 'camera_point_dx')
            dy = self.subtract(camera_decomposer.outputTranslateY, global_sampler_info.pointWorldY, 'camera_point_dy')
            dz = self.subtract(camera_decomposer.outputTranslateZ, global_sampler_info.pointWorldZ, 'camera_point_dz')
            dx2 = self.power(dx, 2, 'camera_point_dx_2')
            dy2 = self.power(dy, 2, 'camera_point_dy_2')
            dz2 = self.power(dz, 2, 'camera_point_dz_2')
            sum_1 = self.add(dx2, dy2, 'dx2_plus_dy2')
            sum_2 = self.add(sum_1, dz2, 'sum_of_squared_dxyz')
            camera_distance = self.power(sum_2, 0.5, 'camera_distance')
            offset_camera_distance = self.subtract(camera_distance, gcn.min_distance, 'offset_camera_distance')

            num_half_distances = self.divide(offset_camera_distance, gcn.half_distance, 'num_half_distances')
            original_color_remaining = self.power(0.9, num_half_distances, 'original_color_remaining')
            atmosphere_color_amount = self.subtract(1, original_color_remaining, 'atmosphere_color_amount')
            atmospheric_perspective_amount = self.multiply(atmosphere_color_amount, gcn.enable, 'atmospheric_perspective_amount')
            atmospheric_perspective_amount >> gcn.atmospheric_perspective_amount


            self.node = gcn
        else:
            self.node = PyNode('global_controls')
    
    def connect_camera(self, camera):
        camera_transform = camera.getTransform()
        camera_shape = camera.getShape()
        
        camera_shape.message >> self.node.camera.camera_message
        camera_transform.worldMatrix[0] >> self.node.camera.world_matrix
        camera_transform.worldInverseMatrix[0] >> self.node.camera.inverse_world_matrix
        camera_shape.focalLength >> self.node.camera.focal_length
        camera_shape.horizontalFilmAperture >> self.node.camera.horizontal_aperture

    def disconnect_camera(self):
        for attr in [self.node.camera.camera_message,
                     self.node.camera.world_matrix,
                     self.node.camera.inverse_world_matrix,
                     self.node.camera.focal_length,
                     self.node.camera.horizontal_aperture]:
            connections = listConnections(attr, source=True, destination=False, plugs=True)
            if connections:
                connections[0] // attr
    
    def reload(self):
        ...


global_controls = GlobalControls({})
gcn = global_controls.node