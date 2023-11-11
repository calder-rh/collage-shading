from pymel.core import *
from internals.network import Network
from internals.shading_controller import ShadingController
from internals.shading_path import relative_path


class TrackingProjectionPlacement(Network):
    relevant_context = ['object', 'facet', 'image']

    def __init__(self, context, screen_placement, facet_image):
        sc = ShadingController({})

        attrs = ['center_ss_x',
                 'center_ss_y',
                 'rotation_ss',
                 'scale_ss',
                 'image_x',
                 'image_y',
                 'image_scale',
                 'aspect_ratio',
                 'translate_frame_u',
                 'translate_frame_v',
                 'repeat_uv',
                 'rotate_uv']

        expr = """
// float $final_size = scale_ss * image_scale;
float $final_size = pow(scale_ss * image_scale, 0.5);
float $final_rotation = rotation_ss;

vector $image_centered_on_object = <<center_ss_x - $final_size / 2, center_ss_y - $final_size / 2>>;

vector $center_of_image_relative_to_target = <<-0.5 * image_x * image_scale, -0.5 * image_y * image_scale>>;

float $final_rotation_radians = deg_to_rad(- $final_rotation);
float $center_of_rotated_image_relative_to_target_x = $center_of_image_relative_to_target.x * cos($final_rotation_radians) - $center_of_image_relative_to_target.y * sin($final_rotation_radians);
float $center_of_rotated_image_relative_to_target_y = $center_of_image_relative_to_target.x * sin($final_rotation_radians) + $center_of_image_relative_to_target.y * cos($final_rotation_radians);
vector $center_of_rotated_image_relative_to_target = <<$center_of_rotated_image_relative_to_target_x, $center_of_rotated_image_relative_to_target_y>>;

vector $center_of_transformed_image_relative_to_target = $center_of_rotated_image_relative_to_target * scale_ss;

vector $center_of_image_ss = $center_of_transformed_image_relative_to_target + $image_centered_on_object;

translate_frame_u = $center_of_image_ss.x + 0.5;
translate_frame_v = aspect_ratio * $center_of_image_ss.y + 0.5;
repeat_uv = 1 / $final_size;
rotate_uv = $final_rotation;
"""

        node = self.expression('placement_values', attrs, expr)
        screen_placement.position_x >> node.center_ss_x
        screen_placement.position_y >> node.center_ss_y
        screen_placement.rotation >> node.rotation_ss
        screen_placement.scale >> node.scale_ss
        node.image_x.set(facet_image.x)
        node.image_y.set(facet_image.y)
        node.image_scale.set(facet_image.scale)
        sc.aspect_ratio >> node.aspect_ratio

        # Create the image placement node
        texture_placement = self.utility('place2dTexture', 'texture_placement')
        # Plug in the values we calculated
        texture_placement.coverageU.set(1)
        sc.aspect_ratio >> texture_placement.coverageV

        node.translate_frame_u >> texture_placement.translateFrameU
        node.translate_frame_v >> texture_placement.translateFrameV
        node.repeat_uv >> texture_placement.repeatU
        node.repeat_uv >> texture_placement.repeatV
        node.rotate_uv >> texture_placement.rotateUV

        self.texture_placement = texture_placement


class TrackingProjection(Network):
    relevant_context = ['object', 'facet', 'image']

    def __init__(self, context, screen_placement, facet_image, reuse_placement):
        if reuse_placement:
            placement_context = {k: v for k, v in context.items() if k != 'image'}
        else:
            placement_context = context
        
        self.build(TrackingProjectionPlacement(placement_context, screen_placement, facet_image))

        # Create the image texture node
        image_texture = self.texture('file', 'image_texture', isColorManaged=True)
        # Set the image file
        image_texture.fileTextureName.set(facet_image.image, type='string')

        # Connect placement to texture
        self.texture_placement.outUV.connect(image_texture.uvCoord)
        self.texture_placement.outUvFilterSize.connect(image_texture.uvFilterSize)
        self.texture_placement.vertexCameraOne.connect(image_texture.vertexCameraOne)
        self.texture_placement.vertexUvOne.connect(image_texture.vertexUvOne)
        self.texture_placement.vertexUvThree.connect(image_texture.vertexUvThree)
        self.texture_placement.vertexUvTwo.connect(image_texture.vertexUvTwo)
        self.texture_placement.coverage.connect(image_texture.coverage)
        self.texture_placement.mirrorU.connect(image_texture.mirrorU)
        self.texture_placement.mirrorV.connect(image_texture.mirrorV)
        self.texture_placement.noiseUV.connect(image_texture.noiseUV)
        self.texture_placement.offset.connect(image_texture.offset)
        self.texture_placement.repeatUV.connect(image_texture.repeatUV)
        self.texture_placement.rotateFrame.connect(image_texture.rotateFrame)
        self.texture_placement.rotateUV.connect(image_texture.rotateUV)
        self.texture_placement.stagger.connect(image_texture.stagger)
        self.texture_placement.translateFrame.connect(image_texture.translateFrame)
        self.texture_placement.wrapU.connect(image_texture.wrapU)
        self.texture_placement.wrapV.connect(image_texture.wrapV)

        # Create the projection
        projection = self.utility('projection', 'projection')
        # Set it to a perspective projection
        projection.projType.set(8)
        # From the desired camera
        ShadingController({}).camera.camera_message.connect(projection.linkedCamera)
        # Set the image
        image_texture.outColor.connect(projection.image)

        self.color = projection.outColor