from pymel.core import *
from internals.network import Network
from internals.shading_controller import ShadingController


class FocalLengthFactor(Network):
    relevant_context = []
    prefix = None

    def __init__(self, _):
        millimeters_per_inch = 25.4
        attrs = ['focal_length',
                 'horizontal_aperture',
                 'focal_length_factor']
        expr = f'focal_length_factor = focal_length / (horizontal_aperture * {millimeters_per_inch});'
        node = self.expression('focal_length_factor', attrs, expr)
        
        sc = self.build(ShadingController({}))
        sc.camera.horizontal_aperture >> node.horizontal_aperture
        sc.camera.focal_length >> node.focal_length        

        self.focal_length_factor = node.focal_length_factor


class ScreenPlacement(Network):
    relevant_context = ['object', 'facet']
    
    def __init__(self, context, world_placement, image_up):
        sc = self.build(ShadingController({}))
        flf = self.build(FocalLengthFactor({}))

        # Find the location of the object in the space of the camera
        obj_center_cs = self.utility('pointMatrixMult', 'obj_center_cs')
        sc.camera.inverse_world_matrix >> obj_center_cs.inMatrix
        world_placement.obj_center_ws >> obj_center_cs.inPoint

        # Find the location of the facet in the space of the camera
        facet_center_cs = self.utility('pointMatrixMult', 'facet_center_cs')
        sc.camera.inverse_world_matrix >> facet_center_cs.inMatrix
        world_placement.facet_center_ws >> facet_center_cs.inPoint

        # Find the location of the orienter in the space of the camera
        orienter_cs = self.utility('pointMatrixMult', 'orienter_cs')
        sc.camera.inverse_world_matrix >> orienter_cs.inMatrix
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
        
float $facet_center_cs_z = -facet_center_cs_z;
float $facet_center_ss_x = focal_length_factor * facet_center_cs_x / $facet_center_cs_z;
float $facet_center_ss_y = focal_length_factor * facet_center_cs_y / $facet_center_cs_z;
vector $facet_center_ss = <<$facet_center_ss_x, $facet_center_ss_y>>;

float $scale_ss = 10 / $facet_center_cs_z;

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
        orienter_cs.outputX >> node.orienter_cs_x
        orienter_cs.outputY >> node.orienter_cs_y
        orienter_cs.outputZ >> node.orienter_cs_z
        flf.focal_length_factor >> node.focal_length_factor
        node.image_up.set(image_up)

        self.position_x = node.position_x
        self.position_y = node.position_y
        self.rotation = node.rotation
        self.scale = node.scale
