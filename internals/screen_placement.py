from pymel.core import *
from internals.network import Network
from internals.global_controls import gcn


class CalculatedScreenPlacement(Network):
    relevant_context = ['mesh', 'facet']
    
    def __init__(self, context, world_placement, image_up):
        # Find the location of the object in the space of the camera
        obj_center_cs = self.utility('pointMatrixMult', 'obj_center_cs')
        gcn.camera.inverse_world_matrix >> obj_center_cs.inMatrix
        world_placement.obj_center_ws >> obj_center_cs.inPoint

        # Find the location of the facet in the space of the camera
        facet_center_cs = self.utility('pointMatrixMult', 'facet_center_cs')
        gcn.camera.inverse_world_matrix >> facet_center_cs.inMatrix
        world_placement.facet_center_ws >> facet_center_cs.inPoint

        # Find the location of the orienter in the space of the camera
        orienter_cs = self.utility('pointMatrixMult', 'orienter_cs')
        gcn.camera.inverse_world_matrix >> orienter_cs.inMatrix
        world_placement.rotation_ws >> orienter_cs.inPoint

        attrs = ['obj_center_cs_x',
                 'obj_center_cs_y',
                 'obj_center_cs_z',
                 'facet_center_cs_x',
                 'facet_center_cs_y',
                 'facet_center_cs_z',
                 'orienter_cs_x',
                 'orienter_cs_y',
                 'orienter_cs_z',
                 'global_scale',
                 'focal_length_factor',
                 'image_up',
                 'position_x',
                 'position_y',
                 'rotation',
                 'scale']
        
        expr = """
float $obj_center_cs_z = -obj_center_cs_z;
float $obj_center_ss_x = focal_length_factor * obj_center_cs_x / $obj_center_cs_z;
float $obj_center_ss_y = focal_length_factor * obj_center_cs_y / $obj_center_cs_z;
vector $obj_center_ss = <<$obj_center_ss_x, $obj_center_ss_y>>;
        
float $facet_center_cs_z = abs(facet_center_cs_z);
float $facet_center_ss_x = focal_length_factor * facet_center_cs_x / $facet_center_cs_z;
float $facet_center_ss_y = focal_length_factor * facet_center_cs_y / $facet_center_cs_z;
vector $facet_center_ss = <<$facet_center_ss_x, $facet_center_ss_y>>;

float $scale_ss = global_scale / $facet_center_cs_z;

float $orienter_cs_z = -orienter_cs_z;
float $orienter_ss_x = focal_length_factor * orienter_cs_x / $orienter_cs_z;
float $orienter_ss_y = focal_length_factor * orienter_cs_y / $orienter_cs_z;
vector $orienter_ss = <<$orienter_ss_x, $orienter_ss_y>>;
vector $direction_ss = $orienter_ss - $obj_center_ss;
float $angle_ss = rad_to_deg(-atan2($direction_ss.y, $direction_ss.x)) - image_up + 90;

position_x = $facet_center_ss.x;
position_y = $facet_center_ss.y;
rotation = $angle_ss;
scale = $scale_ss;
"""
        node = self.expression('screen_placement', attrs, expr)
        obj_center_cs.outputX >> node.obj_center_cs_x
        obj_center_cs.outputY >> node.obj_center_cs_y
        obj_center_cs.outputZ >> node.obj_center_cs_z
        facet_center_cs.outputX >> node.facet_center_cs_x
        facet_center_cs.outputY >> node.facet_center_cs_y
        facet_center_cs.outputZ >> node.facet_center_cs_z
        gcn.texture_scale >> node.global_scale
        orienter_cs.outputX >> node.orienter_cs_x
        orienter_cs.outputY >> node.orienter_cs_y
        orienter_cs.outputZ >> node.orienter_cs_z
        gcn.camera.focal_length_factor >> node.focal_length_factor
        node.image_up.set(image_up)

        self.position_x = node.position_x
        self.position_y = node.position_y
        self.rotation = node.rotation
        self.scale = node.scale


class AnimatedScreenPlacement(Network):
    relevant_context = ['mesh', 'index']

    def __init__(self, _):
        self.position_x_curve = self.make(createNode, 'position_x_curve', 'animCurveTU')
        self.position_x = self.position_x_curve.output
        self.position_y_curve = self.make(createNode, 'position_y_curve', 'animCurveTU')
        self.position_y = self.position_y_curve.output
        self.rotation_curve = self.make(createNode, 'rotation_curve', 'animCurveTU')
        self.rotation = self.rotation_curve.output
        self.scale_curve = self.make(createNode, 'scale_curve', 'animCurveTU')
        self.scale = self.scale_curve.output
    
    def set_key(self, time, x, y, rotation, scale):
        linear = {'tangentInType': 'linear', 'tangentOutType': 'linear'}
        self.position_x_curve.addKey(time, x, **linear)
        self.position_y_curve.addKey(time, y, **linear)
        self.rotation_curve.addKey(time, rotation, **linear)
        self.scale_curve.addKey(time, scale, **linear)
