from pymel.core import *


class ShadingController:
    def __init__(self):
        sc_name = 'shading_controller'
        rscs_name = 'ref_shading_controllers'

        if objExists(sc_name):
            node = PyNode(sc_name)
            self.camera = node.camera
            self.aspect_ratio = node.aspect_ratio
            self.luminance_factor = node.luminance_factor
            self.edge_curve = node.edge_curve
            self.front_curve = node.front_curve
        else:
            node = group(n=sc_name, em=True)

            for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']:
                node.setAttr(attr, k=False, cb=False)

            addAttr(node, ln='camera', at='compound', nc=4)
            addAttr(node, p='camera', ln='camera_message', at='message')
            addAttr(node, p='camera', ln='inverse_world_matrix', at='matrix', dcb=2)
            addAttr(node, p='camera', ln='focal_length', dcb=2, dv=35)
            addAttr(node, p='camera', ln='horizontal_aperture', dcb=2, dv=1.417)
            addAttr(node, ln='aspect_ratio', k=True, dv=16/9, dcb=2)
            addAttr(node, ln='luminance_factor', min=0, smx=1, dv=1, k=True, dcb=2)
            addAttr(node, ln='edge_curve', min=0, smx=0.5, max=1, dv=0.1, k=True)
            addAttr(node, ln='front_curve', min=0, smx=0.5, max=1, dv=0.4, k=True)
            self.camera = node.camera
            self.aspect_ratio = node.aspect_ratio
            self.luminance_factor = node.luminance_factor
            self.luminance_curve = node.luminance_curve

            ref_shading_controllers = ls(regex=f'[^:]+:({sc_name}|{rscs_name})')
            if ref_shading_controllers:
                for sc in ref_shading_controllers:
                    if not sc.getParent():
                        parent(sc, node)
            
            direct_ref_shading_controllers = ls(regex=f'[^:]+:{sc_name}')
            if direct_ref_shading_controllers:
                for sc in direct_ref_shading_controllers:
                    for attr in ['camera_message',
                                 'inverse_world_matrix',
                                 'focal_length',
                                 'horizontal_aperture']:
                        sc_attr = Attribute(sc + '.camera.' + attr)
                        connections = listConnections(sc_attr, source=True, destination=False, plugs=True)
                        if connections:
                            connections[0] // sc_attr
                        self_attr = Attribute(self.camera + '.' + attr)
                        self_attr >> sc_attr
                    self.luminance_factor >> sc.luminance_factor
                    self.aspect_ratio >> sc.aspect_ratio
            
    def connect_camera(self, camera):
        camera_transform = camera.getTransform()
        camera_shape = camera.getShape()
        
        camera_shape.message >> self.camera.camera_message
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
