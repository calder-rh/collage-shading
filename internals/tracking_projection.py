from pymel.core import *
from internals.network import Network
from internals.global_controls import gcn
from internals.utilities import connect_texture_placement


class TrackingProjectionPlacement(Network):
    relevant_context = ['mesh', 'facet', 'image']

    def __init__(self, context, screen_placement, facet_image, mesh, mod=False):
        attrs = ['center_ss_x',
                 'center_ss_y',
                 'rotation_ss',
                 'scale_ss',
                 'image_x',
                 'image_y',
                 'image_scale',
                 'illum_scale',
                 'aspect_ratio',
                 'translate_frame_u',
                 'translate_frame_v',
                 'repeat_uv',
                 'rotate_uv']
        
        if mod:
            u_mod_str = r' % (1 / repeat_uv)'
            v_mod_str = r' % (aspect_ratio / repeat_uv)'
        else:
            u_mod_str = v_mod_str = ''

        expr = f"""
// float $final_size = image_scale * pow(scale_ss, scale_exp);
float $final_size = image_scale * scale_ss * illum_scale;
float $final_rotation = rotation_ss;

vector $image_centered_on_object = <<center_ss_x - $final_size / 2, center_ss_y - $final_size / 2>>;

vector $center_of_image_relative_to_target = <<-0.5 * image_x * image_scale, -0.5 * image_y * image_scale>>;

float $final_rotation_radians = deg_to_rad(- $final_rotation);
float $center_of_rotated_image_relative_to_target_x = $center_of_image_relative_to_target.x * cos($final_rotation_radians) - $center_of_image_relative_to_target.y * sin($final_rotation_radians);
float $center_of_rotated_image_relative_to_target_y = $center_of_image_relative_to_target.x * sin($final_rotation_radians) + $center_of_image_relative_to_target.y * cos($final_rotation_radians);
vector $center_of_rotated_image_relative_to_target = <<$center_of_rotated_image_relative_to_target_x, $center_of_rotated_image_relative_to_target_y>>;

vector $center_of_transformed_image_relative_to_target = $center_of_rotated_image_relative_to_target * scale_ss;

vector $center_of_image_ss = $center_of_transformed_image_relative_to_target + $image_centered_on_object;

repeat_uv = 1 / $final_size;
rotate_uv = $final_rotation;
translate_frame_u = ($center_of_image_ss.x + 0.5){u_mod_str};
translate_frame_v = (aspect_ratio * $center_of_image_ss.y + 0.5){v_mod_str};
"""

        node = self.expression('placement_values', attrs, expr)
        screen_placement.position_x >> node.center_ss_x
        screen_placement.position_y >> node.center_ss_y
        screen_placement.rotation >> node.rotation_ss
        screen_placement.scale >> node.scale_ss
        mesh.scale_factor >> node.illum_scale
        node.image_x.set(facet_image.x)
        node.image_y.set(facet_image.y)
        node.image_scale.set(facet_image.scale)

        gcn.camera.aspect_ratio >> node.aspect_ratio

        # Create the image placement node
        texture_placement = self.utility('place2dTexture', 'texture_placement')
        # Plug in the values we calculated
        texture_placement.coverageU.set(1)
        gcn.camera.aspect_ratio >> texture_placement.coverageV

        node.translate_frame_u >> texture_placement.translateFrameU
        node.translate_frame_v >> texture_placement.translateFrameV
        node.repeat_uv >> texture_placement.repeatU
        node.repeat_uv >> texture_placement.repeatV
        node.rotate_uv >> texture_placement.rotateUV

        self.texture_placement = texture_placement


class TrackingProjection(Network):
    relevant_context = ['mesh', 'facet', 'image']

    def __init__(self, context, screen_placement, facet_image, reuse_placement, mesh, mod=False):
        if reuse_placement:
            placement_context = {k: v for k, v in context.items() if k != 'image'}
        else:
            placement_context = context
        
        self.build(TrackingProjectionPlacement(placement_context, screen_placement, facet_image, mesh, mod=mod))

        # Create the image texture node
        image_texture = self.texture('file', 'image_texture', isColorManaged=True)
        # Set the image file
        image_texture.fileTextureName.set(facet_image.image, type='string')

        # Connect placement to texture
        connect_texture_placement(self.texture_placement, image_texture)

        # Create the projection
        projection = self.utility('projection', 'projection')
        # Set it to a perspective projection
        projection.projType.set(8)
        # From the desired camera
        gcn.camera.camera_message >> projection.linkedCamera
        # Set the image
        image_texture.outColor >> projection.image

        self.color = projection.outColor