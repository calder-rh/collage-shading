from pymel.core import *

from internals.network import Network
from internals.global_controls import gcn
from internals.utilities import connect_texture_placement
from internals.illuminee import Illuminee
from random import random
import math



class GroundSlice(Network):
    relevant_context = ['index']
    delete = ...

    def __init__(self, _, ground, index):
        self.texture_placement = self.utility('place2dTexture', 'texture_placement')
        self.image_texture = self.texture('file', 'image_texture', isColorManaged=True)
        self.projection = self.utility('projection', 'projection')

        connect_texture_placement(self.texture_placement, self.image_texture)

        self.projection.projType.set(8)
        gcn.camera.camera_message >> self.projection.linkedCamera
        self.image_texture.outColor >> self.projection.image

        ...



class Ground(Network):
    relevant_context = ['mesh']

    def __init__(self, context, mesh):
        obj_type = mesh.type()
        if mesh.type() == 'transform':
            mesh = mesh.getShape()

        original_mesh_transformer = self.utility('transformGeometry', 'original_mesh_transformer')
        mesh.outMesh >> original_mesh_transformer.inputGeometry
        mesh.worldMatrix[0] >> original_mesh_transformer.transform
        original_mesh = original_mesh_transformer.outputGeometry

        flattener = self.utility('transformGeometry', 'flattener')
        original_mesh >> flattener.inputGeometry
        flattener_matrix = self.utility('composeMatrix', 'flattener_matrix')
        flattener_matrix.inputScaleY.set(0)
        flattener_matrix.outputMatrix >> flattener.transform
        
        closest_point_to_flattened_ground = self.utility('closestPointOnMesh', 'closest_point_to_flattened_ground')
        flattener.outputGeometry >> closest_point_to_flattened_ground.inMesh
        closest_point_to_flattened_ground.inPositionY.set(0)

        self.in_x = closest_point_to_flattened_ground.inPositionX
        self.in_z = closest_point_to_flattened_ground.inPositionZ
        self.out_u = closest_point_to_flattened_ground.parameterU
        self.out_v = closest_point_to_flattened_ground.parameterV


        uv_to_xyz = self.utility('pointOnPolyConstraint', 'uv_to_xyz')
        target = uv_to_xyz.target[0]
        self.in_u = target.targetU
        self.in_v = target.targetV
        self.out_xyz = uv_to_xyz.constraintTranslate


        illuminee = Illuminee({'obj': context['mesh'] + '_ground'}, mesh)
        illuminee.control_node.gradient_weight.disconnect()
        illuminee.control_node.gradient_weight.set(0)
        illuminee.control_node.angle_weight.disconnect()
        illuminee.control_node.angle_weight.set(1)
        self.lightness = illuminee.control_node.lightness


        self.decompose_camera = self.utility('decomposeMatrix', 'decompose_camera')
        gcn.camera.world_matrix >> self.decompose_camera.inputMatrix
        camera_rotation_matrix = self.utility('composeMatrix', 'camera_rotation_matrix')
        self.decompose_camera.outputRotate >> camera_rotation_matrix.inputRotate
        move_1_z = self.utility('composeMatrix', 'move_1_z')
        move_1_z.inputTranslateZ.set(1)
        move_1_in_camera_direction = self.utility('multMatrix', 'move_1_in_camera_direction')
        move_1_z.outputMatrix >> move_1_in_camera_direction.matrixIn[0]
        camera_rotation_matrix.outputMatrix >> move_1_in_camera_direction.matrixIn[1]
        camera_rotation_calculator = self.utility('decomposeMatrix', 'camera_rotation_calculator')
        move_1_in_camera_direction.matrixSum >> camera_rotation_calculator.inputMatrix
        camera_ground_vector_calculator = self.utility('normalize', 'camera_ground_vector')
        self.camera_ground_vector = camera_ground_vector_calculator.output
        camera_rotation_calculator.outputTranslateX >> camera_ground_vector_calculator.inputX
        camera_rotation_calculator.outputTranslateZ >> camera_ground_vector_calculator.inputZ
        sampler_info = self.utility('samplerInfo', 'sampler_info')
        point_relative_to_camera = self.utility('aiSubtract', 'point_relative_to_camera')
        sampler_info.pointWorld >> point_relative_to_camera.input1
        self.decompose_camera.outputTranslate >> point_relative_to_camera.input2
        depth_calculator = self.utility('aiDot', 'depth_calculator')
        point_relative_to_camera.outColor >> depth_calculator.input1
        self.camera_ground_vector >> depth_calculator.input2
        depth = self.multiply(depth_calculator.outValue, -1, 'depth')

        depth_minus_offset = self.subtract(depth, gcn.slice_offset, 'depth_minus_offset')
        total_depth = self.multiply(gcn.slice_spacing, gcn.slice_count, 'total_depth')
        normalized_depth = self.divide(depth_minus_offset, total_depth, 'normalized_depth')


        ramp = self.utility('aiRampRgb', 'ramp')
        ramp.attr('type').set(0)
        normalized_depth >> ramp.input
        softness = 0.1
        slice_count = gcn.slice_count.get()
        for i in range(slice_count - 1):
            ramp.ramp[2 * i].ramp_Position.set((i + 1 - softness / 2) / slice_count)
            ramp.ramp[2 * i + 1].ramp_Position.set((i + 1 + softness / 2) / slice_count)
        random_color = [random() for _ in range(3)]
        for i in range(slice_count - 1):
            ramp.ramp[2 * i].ramp_Color.set(random_color)
            random_color = [random() for _ in range(3)]
            ramp.ramp[2 * i + 1].ramp_Color.set(random_color)
        

        shader = self.shader('surfaceShader', 'ground_shader')
        ramp.outColor >> shader.outColor

        sg = self.utility('shadingEngine', 'ground_shader_SG')
        shader.outColor >> sg.surfaceShader


        connections = listConnections(mesh, type='shadingEngine')
        if connections:
            old_sg = connections[0]
            for dsm in old_sg.dagSetMembers:
                connection = listConnections(dsm)[0]
                if connection.getShape() == mesh:
                    if mesh.instObjGroups:
                        mesh.instObjGroups[0] // dsm
                        break

        sets(sg, e=True, fe=mesh.getTransform())
    
    def animate(self):
        anim_curve_list = gcn.slice_offset.listConnections(s=True, d=False, type='animCurve')   
        if anim_curve_list:
            delete(anim_curve_list[0])

        playback_min = int(playbackOptions(min=True, q=True))
        playback_max = int(playbackOptions(max=True, q=True))
        
        prev_offset = gcn.initial_slice_offset.get()
        gcn.slice_offset.setKey(t=playback_min, v=gcn.initial_slice_offset.get())
        for frame in range(playback_min + 1, playback_max + 1):
            prev_frame = frame - 1
            r0 = self.decompose_camera.outputTranslate.get(t=prev_frame)
            r1 = self.decompose_camera.outputTranslate.get(t=frame)
            delta_r = [r1c - r0c for r0c, r1c in zip(r0, r1)]
            d0 = self.camera_ground_vector.get(t=prev_frame)
            d1 = self.camera_ground_vector.get(t=frame)
            d_avg = [(d1c + d0c) / 2 for d0c, d1c in zip(d0, d1)]
            dot = sum(delta_r_c * d_avg_c for delta_r_c, d_avg_c in zip(delta_r, d_avg))
            new_offset = prev_offset + dot
            gcn.slice_offset.setKey(t=frame, v=new_offset)
            prev_offset = new_offset





# class GroundUVConverter(Network):
#     relevant_context = []

#     def __init__(self, _):
#         xyz_to_uv_calculator = self.utility('closestPointOnMesh', 'xyz_to_uv_calculator')
#         result = xyz_to_uv_calculator.result
#         gcn.ground_mesh.connect(xyz_to_uv_calculator.inMesh)
#         self.xyz_in = xyz_to_uv_calculator.inPosition
#         self.u_out = result.parameterU
#         self.v_out = result.parameterV

# guc = GroundUVConverter({})


# millimeters_per_inch = 25.4

# def sy_to_xyz(y_interp, time):
#     camera_trans = listConnections(gcn.camera_message, s=True, d=False)[0]
#     camera_shape = camera_trans.getShape()

#     camera_tx = camera_trans.tx.get(t=time)
#     camera_ty = camera_trans.ty.get(t=time)
#     camera_tz = camera_trans.tz.get(t=time)
#     camera_rx = camera_trans.rx.get(t=time)
#     camera_ry = camera_trans.ry.get(t=time)
#     ground_y = gcn.ground_y.get(t=time)
#     vertical_aperture = millimeters_per_inch * camera_shape.horizontalFilmAperture.get() / gcn.camera.aspect_ratio.get()
#     focal_length = camera_shape.focalLength.get(t=time)

#     horizon_screen_y = focal_length * math.tan(-math.radians(camera_rx)) / vertical_aperture
#     screen_y_min = -0.5
#     screen_y_max = min(0.5, horizon_screen_y)
#     screen_y = screen_y_min + (screen_y_max - screen_y_min) * y_interp

#     angle = camera_rx + math.degrees(math.atan(screen_y * vertical_aperture / focal_length))
#     flat_distance = (camera_ty - ground_y) / math.tan(math.radians(angle))
#     flat_x = camera_tx + flat_distance * math.sin(math.radians(camera_ry))
#     flat_y = ground_y
#     flat_z = camera_tz + flat_distance * math.cos(math.radians(camera_ry))

#     return flat_x, flat_y, flat_z