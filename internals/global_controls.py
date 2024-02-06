from pymel.core import *
from internals.network import Network

from internals.invisible import set_visibility_in_render
from internals.sun_pair import SunPairShaders, SunPair
from internals.global_groups import control_groups


class GlobalControls(Network):
    relevant_context = []
    prefix = ''
    delete = False

    node_name = 'global_controls'

    def __init__(self, _):
        is_new = not objExists(self.node_name)

        if is_new:
            lighting_controller_trans, _ = self.poly(polyCube, self.node_name)
            setAttr(lighting_controller_trans.r, l=True)
            lighting_controller_shape = lighting_controller_trans.getShape()
            set_visibility_in_render(lighting_controller_shape, False)
            parent(lighting_controller_trans, control_groups.controls)
            delete(lighting_controller_trans, ch=True)

            light_direction_cone_trans, _ = self.poly(polyCone, 'light_direction_cone', radius=0.4, height=4, heightBaseline=-1, axis=(0, 0, 1))
            light_source_ball_trans, _ = self.poly(polySphere, 'light_source_ball', radius=0.2, axis=(0, 0, 1))
            light_source_ball_trans.tz.set(3.9)
            light_direction_trans, _ = polyUnite(light_direction_cone_trans, light_source_ball_trans, n='light_direction')
            light_direction_shape = light_direction_trans.getShape()
            delete(light_direction_trans, ch=True)

            initial_sg_connection = listConnections(light_direction_shape, s=False, c=True, p=True)[0]
            initial_sg_connection[0] // initial_sg_connection[1]
            sun_sg = SunPairShaders({}).sun_sg
            sets(sun_sg, e=True, fe=light_direction_shape)
            parent(light_direction_trans, lighting_controller_trans)
            setAttr(light_direction_trans.t, l=True)
            setAttr(light_direction_trans.s, l=True)
            set_visibility_in_render(light_direction_shape, False)

            gcn = lighting_controller_trans
            addAttr(gcn, ln='gradients_weight', min=0, smx=1, dv=1)
            addAttr(gcn, ln='lights_weight', min=0, smx=1, dv=1)
            addAttr(gcn, ln='shadow_influences_weight', min=0, smx=1, dv=0.5)
            addAttr(gcn, ln='adjustment', min=-1, max=1, dv=0)

            addAttr(gcn, ln='shadow_influences_distance', min=0, smx=1, dv=1)

            addAttr(gcn, ln='front_value_range', at='compound', nc=2)
            addAttr(gcn, p='front_value_range', ln='front_min', min=0, max=1, dv=0)
            addAttr(gcn, p='front_value_range', ln='front_max', min=0, max=1, dv=1)

            addAttr(gcn, ln='back_value_range', at='compound', nc=2)
            addAttr(gcn, p='back_value_range', ln='back_min', min=0, max=1, dv=0.3)
            addAttr(gcn, p='back_value_range', ln='back_max', min=0, max=1, dv=0.7)

            addAttr(gcn, ln='default_lightness', min=0, max=1, dv=0.5)

            addAttr(gcn, ln='ground_y', smn=-10, smx=10, dv=0, k=True)

            addAttr(gcn, ln='sun_distance', min=0, smx=1000, dv=100)
            
            addAttr(gcn, ln='atmospheric_perspective', at='compound', nc=3)
            addAttr(gcn, p='atmospheric_perspective', ln='enable', at='bool')
            addAttr(gcn, p='atmospheric_perspective', ln='half_distance', min=1, smx=1000, dv=100)
            addAttr(gcn, p='atmospheric_perspective', ln='color', at='float3', uac=True)
            addAttr(gcn, ln='colorR', at='float', parent='color')
            addAttr(gcn, ln='colorG', at='float', parent='color')
            addAttr(gcn, ln='colorB', at='float', parent='color')
            lighting_controller_trans.atmospheric_perspective.color.set(0.5, 0.7, 1)

            addAttr(gcn, ln='camera', at='compound', nc=6)
            addAttr(gcn, p='camera', ln='camera_message', at='message')
            addAttr(gcn, p='camera', ln='world_matrix', at='matrix')
            addAttr(gcn, p='camera', ln='inverse_world_matrix', at='matrix')
            addAttr(gcn, p='camera', ln='focal_length', dv=35)
            addAttr(gcn, p='camera', ln='horizontal_aperture', dv=1.417)
            addAttr(gcn, p='camera', ln='aspect_ratio', k=True, dv=16/9)

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

            addAttr(gcn, ln='ground_mesh', dt='mesh')

            light_sun_pair = SunPair({'usage': 'light'}, light_direction_trans.r, gcn.sun_distance, make_objects=True)
            camera_rotation_calculator = self.utility('decomposeMatrix', 'camera_rotation_calculator')
            gcn.camera.world_matrix >> camera_rotation_calculator.inputMatrix
            camera_sun_pair = SunPair({'usage': 'camera'}, camera_rotation_calculator.outputRotate, gcn.sun_distance)

            light_sun_pair.sun_position >> gcn.suns.light_sun_position
            light_sun_pair.antisun_position >> gcn.suns.light_antisun_position
            light_sun_pair.direction_inverse_matrix >> gcn.suns.light_direction_inverse_matrix
            light_sun_pair.surface_point_z >> gcn.suns.light_surface_point_z
            camera_sun_pair.sun_position >> gcn.suns.camera_sun_position
            camera_sun_pair.antisun_position >> gcn.suns.camera_antisun_position
            camera_sun_pair.direction_inverse_matrix >> gcn.suns.camera_direction_inverse_matrix
            camera_sun_pair.surface_point_z >> gcn.suns.camera_surface_point_z

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