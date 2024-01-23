from pymel.core import *
from internals.network import Network

from internals.control_groups import control_groups
from internals.invisible import make_invisible_in_render
from internals.sun_pair import SunPair, SunPairShaders



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
            make_invisible_in_render(lighting_controller_shape)
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
            make_invisible_in_render(light_direction_shape)

            gc = lighting_controller_trans
            addAttr(gc, ln='gradients', min=0, smx=1, dv=1)
            addAttr(gc, ln='lights', min=0, smx=1, dv=1)
            addAttr(gc, ln='shadow_influences', min=0, smx=1, dv=1)

            addAttr(gc, ln='front_value_range', at='compound', nc=2)
            addAttr(gc, p='front_value_range', ln='front_min', min=0, max=1, dv=0)
            addAttr(gc, p='front_value_range', ln='front_max', min=0, max=1, dv=1)

            addAttr(gc, ln='back_value_range', at='compound', nc=2)
            addAttr(gc, p='back_value_range', ln='back_min', min=0, max=1, dv=0.3)
            addAttr(gc, p='back_value_range', ln='back_max', min=0, max=1, dv=0.7)

            addAttr(gc, ln='sun_distance', min=0, smx=1000, dv=100)
            
            addAttr(gc, ln='atmospheric_perspective', at='compound', nc=3)
            addAttr(gc, p='atmospheric_perspective', ln='enable', at='bool')
            addAttr(gc, p='atmospheric_perspective', ln='half_distance', min=1, smx=1000, dv=100)
            addAttr(gc, p='atmospheric_perspective', ln='color', at='float3', uac=True)
            addAttr(gc, ln='colorR', at='float', parent='color')
            addAttr(gc, ln='colorG', at='float', parent='color')
            addAttr(gc, ln='colorB', at='float', parent='color')
            lighting_controller_trans.atmospheric_perspective.color.set(0.5, 0.7, 1)

            addAttr(gc, ln='camera', at='compound', nc=6)
            addAttr(gc, p='camera', ln='camera_message', at='message')
            addAttr(gc, p='camera', ln='world_matrix', at='matrix')
            addAttr(gc, p='camera', ln='inverse_world_matrix', at='matrix')
            addAttr(gc, p='camera', ln='focal_length', dv=35)
            addAttr(gc, p='camera', ln='horizontal_aperture', dv=1.417)
            addAttr(gc, p='camera', ln='aspect_ratio', k=True, dv=16/9)

            addAttr(gc, ln='suns', at='compound', nc=8)
            addAttr(gc, p='suns', ln='light_sun_position', at='float3')
            addAttr(gc, ln='light_sun_position_x', at='float', p='light_sun_position')
            addAttr(gc, ln='light_sun_position_y', at='float', p='light_sun_position')
            addAttr(gc, ln='light_sun_position_z', at='float', p='light_sun_position')
            addAttr(gc, p='suns', ln='light_antisun_position', at='float3')
            addAttr(gc, ln='light_antisun_position_x', at='float', p='light_antisun_position')
            addAttr(gc, ln='light_antisun_position_y', at='float', p='light_antisun_position')
            addAttr(gc, ln='light_antisun_position_z', at='float', p='light_antisun_position')
            addAttr(gc, ln='light_direction_inverse_matrix', at='matrix', p='suns')
            addAttr(gc, ln='light_surface_point_z', p='suns')
            addAttr(gc, p='suns', ln='camera_sun_position', at='float3')
            addAttr(gc, ln='camera_sun_position_x', at='float', p='camera_sun_position')
            addAttr(gc, ln='camera_sun_position_y', at='float', p='camera_sun_position')
            addAttr(gc, ln='camera_sun_position_z', at='float', p='camera_sun_position')
            addAttr(gc, p='suns', ln='camera_antisun_position', at='float3')
            addAttr(gc, ln='camera_antisun_position_x', at='float', p='camera_antisun_position')
            addAttr(gc, ln='camera_antisun_position_y', at='float', p='camera_antisun_position')
            addAttr(gc, ln='camera_antisun_position_z', at='float', p='camera_antisun_position')
            addAttr(gc, ln='camera_direction_inverse_matrix', at='matrix', p='suns')
            addAttr(gc, ln='camera_surface_point_z', p='suns')

            addAttr(gc, ln='collage_lights', m=True)

            light_sun_pair = SunPair({'usage': 'light'}, light_direction_trans.r, gc.sun_distance, make_objects=True)
            camera_rotation_calculator = self.utility('decomposeMatrix', 'camera_rotation_calculator')
            camera_sun_pair = SunPair({'usage': 'camera'}, camera_rotation_calculator.outputRotate, gc.sun_distance)

            light_sun_pair.sun_position >> gc.suns.light_sun_position
            light_sun_pair.antisun_position >> gc.suns.light_antisun_position
            light_sun_pair.direction_inverse_matrix >> gc.suns.light_direction_inverse_matrix
            light_sun_pair.surface_point_z >> gc.suns.light_surface_point_z
            camera_sun_pair.sun_position >> gc.suns.camera_sun_position
            camera_sun_pair.antisun_position >> gc.suns.camera_antisun_position
            camera_sun_pair.direction_inverse_matrix >> gc.suns.camera_direction_inverse_matrix
            camera_sun_pair.surface_point_z >> gc.suns.camera_surface_point_z

            self.node = gc
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