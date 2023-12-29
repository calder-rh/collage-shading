from pymel.core import *

from internals.control_groups import ControlGroups


class ShadingController:
    def __init__(self):
        sc_name = 'shading_controller'
        rscs_name = 'ref_shading_controllers'

        if objExists(sc_name):
            node = PyNode(sc_name)
            self.camera = node.camera
            self.aspect_ratio = self.camera.aspect_ratio
            self.suns = node.suns
            self.value_ranges = node.value_ranges
            self.atmospheric_perspective = node.atmospheric_perspective
        else:
            node = group(n=sc_name, em=True)

            cg = ControlGroups({})
            parent(node, cg.internals)

            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']:
                node.setAttr(attr, k=False, cb=False)

            addAttr(node, ln='camera', at='compound', nc=6)
            addAttr(node, p='camera', ln='camera_message', at='message')
            addAttr(node, p='camera', ln='world_matrix', at='matrix', dcb=2)
            addAttr(node, p='camera', ln='inverse_world_matrix', at='matrix', dcb=2)
            addAttr(node, p='camera', ln='focal_length', dcb=2, dv=35)
            addAttr(node, p='camera', ln='horizontal_aperture', dcb=2, dv=1.417)
            addAttr(node, p='camera', ln='aspect_ratio', k=True, dv=16/9, dcb=2)

            addAttr(node, ln='suns', at='compound', nc=9)
            addAttr(node, p='suns', ln='sun_distance')
            addAttr(node, p='suns', ln='light_sun_position', at='float3')
            addAttr(node, ln='light_sun_position_x', at='float', p='light_sun_position')
            addAttr(node, ln='light_sun_position_y', at='float', p='light_sun_position')
            addAttr(node, ln='light_sun_position_z', at='float', p='light_sun_position')
            addAttr(node, p='suns', ln='light_antisun_position', at='float3')
            addAttr(node, ln='light_antisun_position_x', at='float', p='light_antisun_position')
            addAttr(node, ln='light_antisun_position_y', at='float', p='light_antisun_position')
            addAttr(node, ln='light_antisun_position_z', at='float', p='light_antisun_position')
            addAttr(node, ln='light_direction_inverse_matrix', at='matrix', p='suns')
            addAttr(node, ln='light_surface_point_z', p='suns')
            addAttr(node, p='suns', ln='camera_sun_position', at='float3')
            addAttr(node, ln='camera_sun_position_x', at='float', p='camera_sun_position')
            addAttr(node, ln='camera_sun_position_y', at='float', p='camera_sun_position')
            addAttr(node, ln='camera_sun_position_z', at='float', p='camera_sun_position')
            addAttr(node, p='suns', ln='camera_antisun_position', at='float3')
            addAttr(node, ln='camera_antisun_position_x', at='float', p='camera_antisun_position')
            addAttr(node, ln='camera_antisun_position_y', at='float', p='camera_antisun_position')
            addAttr(node, ln='camera_antisun_position_z', at='float', p='camera_antisun_position')
            addAttr(node, ln='camera_direction_inverse_matrix', at='matrix', p='suns')
            addAttr(node, ln='camera_surface_point_z', p='suns')

            addAttr(node, ln='value_ranges', at='compound', nc=4)
            addAttr(node, p='value_ranges', ln='front_min')
            addAttr(node, p='value_ranges', ln='front_max')
            addAttr(node, p='value_ranges', ln='back_min')
            addAttr(node, p='value_ranges', ln='back_max')

            addAttr(node, ln='atmospheric_perspective', at='compound', nc=3)
            addAttr(node, p='atmospheric_perspective', ln='enable', at='bool')
            addAttr(node, p='atmospheric_perspective', ln='half_distance')
            addAttr(node, p='atmospheric_perspective', ln='color', at='float3', uac=True)
            addAttr(node, ln='colorR', at='float', parent='color')
            addAttr(node, ln='colorG', at='float', parent='color')
            addAttr(node, ln='colorB', at='float', parent='color')
            
            self.camera = node.camera
            self.aspect_ratio = self.camera.aspect_ratio
            self.suns = node.suns
            self.value_ranges = node.value_ranges
            self.atmospheric_perspective = node.atmospheric_perspective

            ref_shading_controllers = ls(regex=f'[^:]+:({sc_name}|{rscs_name})')
            if ref_shading_controllers:
                for sc in ref_shading_controllers:
                    if not sc.getParent():
                        parent(sc, node)
            
            direct_ref_shading_controllers = ls(regex=f'[^:]+:{sc_name}')
            if direct_ref_shading_controllers:
                for sc in direct_ref_shading_controllers:
                    for attr in ['camera.camera_message',
                                 'camera.world_matrix',
                                 'camera.inverse_world_matrix',
                                 'camera.focal_length',
                                 'camera.horizontal_aperture',
                                 'camera.aspect_ratio',
                                 
                                 'suns.sun_distance',
                                 'suns.light_sun_position',
                                 'suns.light_antisun_position',
                                 'suns.camera_sun_position',
                                 'suns.camera_antisun_position',

                                 'value_ranges.front_min',
                                 'value_ranges.front_max',
                                 'value_ranges.back_min',
                                 'value_ranges.back_max',
                                 
                                 'atmospheric_perspective.enable',
                                 'atmospheric_perspective.half_distance'
                                 'atmospheric_perspective.color',
                                 'atmospheric_perspective.colorR',
                                 'atmospheric_perspective.colorG',
                                 'atmospheric_perspective.colorB']:
                        sc_attr = Attribute(sc + '.' + attr)
                        connections = listConnections(sc_attr, source=True, destination=False, plugs=True)
                        if connections:
                            connections[0] // sc_attr
                        self_attr = Attribute(node + '.' + attr)
                        self_attr >> sc_attr
            
    def connect_camera(self, camera):
        camera_transform = camera.getTransform()
        camera_shape = camera.getShape()
        
        camera_shape.message >> self.camera.camera_message
        camera_transform.worldMatrix[0] >> self.camera.world_matrix
        camera_transform.worldInverseMatrix[0] >> self.camera.inverse_world_matrix
        camera_shape.focalLength >> self.camera.focal_length
        camera_shape.horizontalFilmAperture >> self.camera.horizontal_aperture

    def disconnect_camera(self):
        for attr in [self.camera.camera_message,
                     self.camera.inverse_world_matrix,
                     self.camera.focal_length,
                     self.camera.horizontal_aperture]:
            connections = listConnections(attr, source=True, destination=False, plugs=True)
            if connections:
                connections[0] // attr
