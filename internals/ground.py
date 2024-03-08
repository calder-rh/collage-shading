from pymel.core import *

from internals.network import Network
from internals.global_controls import gcn
from internals.global_groups import lighting_sets
from internals.illuminee import Illuminee
from internals.screen_placement import AnimatedScreenPlacement
from internals.tracking_projection import TrackingProjection
from internals import palettes

from random import uniform
from itertools import islice


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


# # x_ss_samples = [i / 10 for i in range(-5, 6, 1)]
# x_ss_samples = [i / 10 for i in range(-4, 6, 2)]
# x_ss_samples = [-0.45, -0.15, 0.15, 0.45]
x_ss_samples = [-0.4, 0, 0.4]

class GroundBand(Network):
    relevant_context = ['mesh', 'index']

    def __init__(self, context, ground, index):
        self.ground = ground
        self.index = index

        self.screen_placement = AnimatedScreenPlacement({'mesh': context['mesh'], 'index': str(self.index)})

        palette = palettes.get_palette(palettes.ground_palette_path())
        palette.make(1, (0.5, 0.5))

        shade_ramp = self.utility('aiRampRgb', 'shade_ramp')
        shade_ramp.attr('type').set(0)
        self.ground.lightness >> shade_ramp.input

        for shade_index, (facet_image, luminance_value) in enumerate(zip(palette.facet_images, palette.luminance_values)):
            start_index = 2 * shade_index
            end_index = start_index + 1
            shade_ramp.ramp[start_index].ramp_Position.set(luminance_value[0])
            shade_ramp.ramp[end_index].ramp_Position.set(luminance_value[1])

            tracking_projection_context = context | {'facet': context['index'], 'image': f'shade{shade_index}'}
            tracking_projection = self.build(TrackingProjection(tracking_projection_context, self.screen_placement, facet_image, isinstance(palette, palettes.ImagesPalette)), add_keys=False)

            tracking_projection.color >> shade_ramp.ramp[start_index].ramp_Color
            tracking_projection.color >> shade_ramp.ramp[end_index].ramp_Color
        
        self.color = shade_ramp.outColor


    def z_gs(self, frame):
        return -(gcn.band_offset.get(t=frame) + gcn.band_spacing.get() * (self.index + 0.5))


    def x_ss_to_ground_xyz_ws(self, x_ss, frame):
        z_gs = self.z_gs(frame)
        x_gs = z_gs * x_ss / gcn.focal_length_factor.get(t=frame)
        z_unit = self.ground.camera_ground_vector.get(t=frame)
        x_unit = (-z_unit[2], 0, z_unit[0])
        camera_ground = self.ground.decompose_camera.outputTranslate.get(t=frame)
        camera_ground[1] = 0
        return tuple(z_gs * zuc + x_gs * xuc + cc for zuc, xuc, cc in zip(z_unit, x_unit, camera_ground))
    

    def ground_xyz_ws_to_uv(self, xyz_ws, frame):
        self.ground.xyz_ws_to_uv.set(xyz_ws)
        return self.ground.u_from_xyz_ws.get(t=frame), self.ground.v_from_xyz_ws.get(t=frame)
    

    def uv_to_xyz_ws(self, uv, frame):
        self.ground.uv_to_xyz_ws.set(uv)
        return self.ground.xyz_ws_from_uv.get(t=frame)
    

    def xyz_ws_to_xy_ss(self, xyz, frame):
        self.ground.xyz_ws_to_xyz_cs.set(xyz)
        x_cs, y_cs, z_cs = self.ground.xyz_cs_from_xyz_ws.get(t=frame)
        x_ss = x_cs * gcn.focal_length_factor.get(t=frame) / (-z_cs)
        y_ss = y_cs * gcn.focal_length_factor.get(t=frame) / (-z_cs)
        return x_ss, y_ss
    

    def xyz_to_normal(self, xyz): 
        self.ground.xyz_ws_to_vertex.set(xyz)
        vertex = self.ground.vertex_from_xyz_ws.get()
        select(self.ground.mesh.vtx[vertex])
        normals = polyNormalPerVertex(q=True, xyz=True)
        # return [sum([normal[c] for normal in batched(normals, 3)]) / (len(normals) / 3) for c in range(3)]
        return [sum(c) / (len(normals) / 3) for c in zip(*batched(normals, 3))]
    

    def animate(self):
        playback_min = int(playbackOptions(min=True, q=True))
        playback_max = int(playbackOptions(max=True, q=True))

        x_ss = uniform(-0.5, 0.5)
        y_ss = uniform(-0.5, 0.5)
        scale = abs(gcn.texture_scale.get(t=playback_min) / self.z_gs(playback_min))
        self.screen_placement.set_key(playback_min, x_ss, y_ss, 0, scale)
    
        # x_ss_samples = [i / 10 for i in range(-4, 6, 2)]
        # x_ss_samples = [0]
        # x_ss_samples = [-0.3, 0, 0.3]

        for frame in range(playback_min + 1, playback_max + 1):
            xy_ss_list = []

            for sample_index, sample in enumerate(x_ss_samples):
                ground_xyz = self.x_ss_to_ground_xyz_ws(sample, frame)
                ground_x, _, ground_z = ground_xyz
                uv = self.ground_xyz_ws_to_uv(ground_xyz, frame)
                
                prev_xyz_ws = self.uv_to_xyz_ws(uv, frame - 1)
                current_xyz_ws = self.uv_to_xyz_ws(uv, frame)
                x, _, z = current_xyz_ws
                error = ((x - ground_x) ** 2 + (z - ground_z) ** 2) ** 0.5
                if error > 2:
                    continue
                
                prev_xy_ss = self.xyz_ws_to_xy_ss(prev_xyz_ws, frame - 1)
                current_xy_ss = self.xyz_ws_to_xy_ss(current_xyz_ws, frame)
                xy_ss_list.append((prev_xy_ss, current_xy_ss))
                # Δxy_ss = (current_xy_ss[0] - prev_xy_ss[0], current_xy_ss[1] - prev_xy_ss[1])
                # Δxy_ss_list.append(Δxy_ss)

            prev_cam_trans = self.ground.decompose_camera.outputTranslate.get(t=frame - 1)
            current_cam_trans = self.ground.decompose_camera.outputTranslate.get(t=frame)
            prev_dist = sum([(cam_c - band_c) ** 2 for cam_c, band_c in zip(prev_cam_trans, prev_xyz_ws)]) ** 0.5
            current_dist = sum([(cam_c - band_c) ** 2 for cam_c, band_c in zip(current_cam_trans, current_xyz_ws)]) ** 0.5
            scale_factor = prev_dist / current_dist
            scale *= scale_factor
            
            if not xy_ss_list:
                continue

            dx_avg, dy_avg = [sum(p2[c] - p1[c] for p1, p2 in xy_ss_list) / len(xy_ss_list) for c in range(2)]

            if scale_factor == 1:
                x_ss += dx_avg
                y_ss += dy_avg
                self.screen_placement.set_key(frame, x_ss, y_ss, 0, scale)
            else:
                x_avg, y_avg = [sum(p2[c] for _, p2 in xy_ss_list) / len(xy_ss_list) for c in range(2)]
                x_piv = x_avg - dx_avg / (scale_factor - 1)
                y_piv = y_avg - dy_avg / (scale_factor - 1)
                x_ss = x_piv + (x_ss - x_piv) * scale_factor
                y_ss = y_piv + (y_ss - y_piv) * scale_factor
                self.screen_placement.set_key(frame, x_ss, y_ss, 0, scale)


class Ground(Network):
    relevant_context = ['mesh']

    def __init__(self, context, mesh):
        self.mesh = mesh
        obj_type = self.mesh.type()
        if self.mesh.type() == 'transform':
            self.mesh = self.mesh.getShape()

        original_mesh_transformer = self.utility('transformGeometry', 'original_mesh_transformer')
        self.mesh.outMesh >> original_mesh_transformer.inputGeometry
        self.mesh.worldMatrix[0] >> original_mesh_transformer.transform
        original_mesh = original_mesh_transformer.outputGeometry

        flattener = self.utility('transformGeometry', 'flattener')
        original_mesh >> flattener.inputGeometry
        flattener_matrix = self.utility('composeMatrix', 'flattener_matrix')
        flattener_matrix.inputScaleY.set(0)
        flattener_matrix.outputMatrix >> flattener.transform
        
        closest_point_to_flattened_ground = self.utility('closestPointOnMesh', 'closest_point_to_flattened_ground')
        flattener.outputGeometry >> closest_point_to_flattened_ground.inMesh

        closest_point_to_regular_ground = self.utility('closestPointOnMesh', 'closest_point_to_regular_ground')
        original_mesh >> closest_point_to_regular_ground.inMesh

        self.xyz_ws_to_uv = closest_point_to_flattened_ground.inPosition
        self.u_from_xyz_ws = closest_point_to_flattened_ground.parameterU
        self.v_from_xyz_ws = closest_point_to_flattened_ground.parameterV


        uv_to_xyz = self.utility('pointOnPolyConstraint', 'uv_to_xyz')
        target = uv_to_xyz.target[0]
        original_mesh >> target.targetMesh
        self.uv_to_xyz_ws = target.targetUV
        self.xyz_ws_from_uv = uv_to_xyz.constraintTranslate


        ws_to_cs = self.utility('pointMatrixMult', 'world_space_to_cam_space')
        gcn.camera.inverse_world_matrix >> ws_to_cs.inMatrix
        self.xyz_ws_to_xyz_cs = ws_to_cs.inPoint
        self.xyz_cs_from_xyz_ws = ws_to_cs.output


        self.xyz_ws_to_vertex = closest_point_to_regular_ground.inPosition
        self.vertex_from_xyz_ws = closest_point_to_regular_ground.closestVertexIndex


        illuminee = Illuminee({'obj': context['mesh'] + '_ground'}, self.mesh)
        illuminee.control_node.gradient_weight.disconnect()
        illuminee.control_node.gradient_weight.set(0)
        illuminee.control_node.lights_weight.disconnect()
        illuminee.control_node.lights_weight.set(0.5)
        illuminee.control_node.angle_weight.disconnect()
        illuminee.control_node.angle_weight.set(0.5)
        illuminee.control_node.min_saturation.disconnect()
        illuminee.control_node.min_saturation.set(1)
        self.lightness = illuminee.control_node.lightness

        sets(lighting_sets.global_set, add=illuminee.control_node.angle_remap.get())

        self.decompose_camera = self.utility('decomposeMatrix', 'decompose_camera')
        gcn.camera.world_matrix >> self.decompose_camera.inputMatrix
        camera_ground_vector_calculator = self.utility('normalize', 'camera_ground_vector')
        gcn.camera_direction_vector_x >> camera_ground_vector_calculator.inputX
        gcn.camera_direction_vector_z >> camera_ground_vector_calculator.inputZ
        self.camera_ground_vector = camera_ground_vector_calculator.output
        sampler_info = self.utility('samplerInfo', 'sampler_info')
        point_relative_to_camera = self.utility('aiSubtract', 'point_relative_to_camera')
        sampler_info.pointWorld >> point_relative_to_camera.input1
        self.decompose_camera.outputTranslate >> point_relative_to_camera.input2
        depth_calculator = self.utility('aiDot', 'depth_calculator')
        point_relative_to_camera.outColor >> depth_calculator.input1
        self.camera_ground_vector >> depth_calculator.input2
        depth = self.multiply(depth_calculator.outValue, -1, 'depth')

        depth_minus_offset = self.subtract(depth, gcn.band_offset, 'depth_minus_offset')
        total_depth = self.multiply(gcn.band_spacing, gcn.band_count, 'total_depth')
        normalized_depth = self.divide(depth_minus_offset, total_depth, 'normalized_depth')

        
        self.bands = [GroundBand(context | {'index': str(i)}, self, i) for i in range(gcn.band_count.get())]


        ramp = self.utility('aiRampRgb', 'ramp')
        ramp.attr('type').set(0)
        normalized_depth >> ramp.input
        softness = 0.4
        band_count = gcn.band_count.get()

        for i in range(band_count - 1):
            ramp.ramp[2 * i].ramp_Position.set((i + 1 - softness / 2) / band_count)
            self.bands[i].color >> ramp.ramp[2 * i].ramp_Color
            ramp.ramp[2 * i + 1].ramp_Position.set((i + 1 + softness / 2) / band_count)
            self.bands[i + 1].color >> ramp.ramp[2 * i + 1].ramp_Color
        
        shader = self.shader('surfaceShader', 'ground_shader')
        ramp.outColor >> shader.outColor

        sg = self.utility('shadingEngine', 'ground_shader_SG')
        shader.outColor >> sg.surfaceShader


        connections = listConnections(self.mesh, type='shadingEngine')
        if connections:
            old_sg = connections[0]
            for dsm in old_sg.dagSetMembers:
                connection = listConnections(dsm)[0]
                if connection.getShape() == self.mesh:
                    if self.mesh.instObjGroups:
                        self.mesh.instObjGroups[0] // dsm
                        break

        sets(sg, e=True, fe=self.mesh.getTransform())
    

    def animate(self):
        anim_curve_list = gcn.band_offset.listConnections(s=True, d=False, type='animCurve')   
        if anim_curve_list:
            delete(anim_curve_list[0])

        playback_min = int(playbackOptions(min=True, q=True))
        playback_max = int(playbackOptions(max=True, q=True))
        
        prev_offset = gcn.initial_band_offset.get()
        gcn.band_offset.setKey(t=playback_min, v=gcn.initial_band_offset.get())
        for frame in range(playback_min + 1, playback_max + 1):
            prev_frame = frame - 1
            r0 = self.decompose_camera.outputTranslate.get(t=prev_frame)
            r1 = self.decompose_camera.outputTranslate.get(t=frame)
            Δr = [r1c - r0c for r0c, r1c in zip(r0, r1)]
            d0 = self.camera_ground_vector.get(t=prev_frame)
            d1 = self.camera_ground_vector.get(t=frame)
            d_avg = [(d1c + d0c) / 2 for d0c, d1c in zip(d0, d1)]
            dot = sum(delta_r_c * d_avg_c for delta_r_c, d_avg_c in zip(Δr, d_avg))
            new_offset = prev_offset + dot
            gcn.band_offset.setKey(t=frame, v=new_offset)
            prev_offset = new_offset
        
        for band in self.bands:
            band.animate()
