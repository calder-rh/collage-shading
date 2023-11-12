from pymel.core import *
from internals.network import Network
from internals import palettes
from internals.world_placement import RigidWorldPlacement
from internals.screen_placement import ScreenPlacement
from internals.tracking_projection import TrackingProjection
from internals.shading_controller import ShadingController
from internals.shading_path import relative_path
import json

solid_region = 0.05
noise_scale = 300
noise_adjustment = 0.1


class Luminance(Network):
    relevant_context = []
    delete = False

    def __init__(self, context):
        raw_luminance = self.utility('surfaceLuminance', 'raw_luminance')
        sc = ShadingController({})
        scaled_luminance = self.multiply(raw_luminance.outValue, sc.luminance_factor, 'scaled_luminance')

        noise = self.utility('aiNoise', 'luminance_noise')
        noise.coordSpace.set(3)
        y_scale = noise_scale
        x_scale = self.multiply(noise_scale, sc.aspect_ratio, 'u_scale')
        x_scale >> noise.scaleX
        noise.scaleY.set(y_scale)

        noise_projection = self.utility('projection', 'noise_projection')
        noise_projection.projType.set(8)
        sc.camera.camera_message >> noise_projection.linkedCamera
        noise.outColor >> noise_projection.image

        adjusted_noise = self.utility('remapValue', 'adjusted_noise')
        adjusted_noise.outputMin.set(-noise_adjustment)
        adjusted_noise.outputMax.set(noise_adjustment)
        noise_projection.outColorR >> adjusted_noise.inputValue

        noisy_luminance = self.add(scaled_luminance, adjusted_noise.outValue, 'noisy_luminance')
        # TODO which do we want?
        self.luminance = scaled_luminance


class FacetShader(Network):
    relevant_context = ['object', 'facet']
    
    def __init__(self, context, masks_path, resolution, obj, facet_index, facet_settings, facet_center):
        multiple_facets = masks_path is not None

        palette = palettes.get_palette(facet_settings['palette'])
        palette.make(facet_settings['scale'], facet_settings['edge distance'])

        world_placement = self.build(RigidWorldPlacement(context, obj, facet_center, facet_settings['object up']))
        if (facet_up := facet_settings['image up']) is not None:
            image_up = facet_up
            print(image_up)
        else:
            image_up = palette.settings()['up']
        screen_placement = self.build(ScreenPlacement(context, world_placement, image_up))

        shade_ramp = self.utility('aiRampRgb', 'shade_ramp')
        setAttr(f'{shade_ramp.name()}.type', 0)
        self.build(Luminance({})).luminance >> shade_ramp.input

        for shade_index, (facet_image, luminance_value) in enumerate(zip(palette.facet_images, palette.luminance_values)):
            start_index = 2 * shade_index
            end_index = start_index + 1
            adjusted_luminance_value = solid_region / 2 + luminance_value * (1 - solid_region)
            shade_ramp.ramp[start_index].ramp_Position.set(adjusted_luminance_value - solid_region / 2)
            shade_ramp.ramp[end_index].ramp_Position.set(adjusted_luminance_value + solid_region / 2)

            tracking_projection_context = context | {'image': f'shade{shade_index}'}
            tracking_projection = self.build(TrackingProjection(tracking_projection_context, screen_placement, facet_image, isinstance(palette, palettes.ImagesPalette)), add_keys=False)

            tracking_projection.color >> shade_ramp.ramp[start_index].ramp_Color
            tracking_projection.color >> shade_ramp.ramp[end_index].ramp_Color

        if multiple_facets:
            facet_mask = self.texture('file', f'facet{facet_index}', isColorManaged=True)
            facet_mask.fileTextureName.set(masks_path / f'{facet_index}.png', type='string')
            repeat_uv = resolution / (resolution + 2)
            offset = (1 - repeat_uv) / 2
            facet_mask.repeatU.set(repeat_uv)
            facet_mask.repeatV.set(repeat_uv)
            facet_mask.offsetU.set(offset)
            facet_mask.offsetV.set(offset)
            corrected_facet_mask = self.utility('gammaCorrect', f'g_facet{facet_index}')
            facet_mask.outColor >> corrected_facet_mask.value
            corrected_facet_mask.gamma.set((2,) * 3)

            masked_shade_ramp = self.utility('aiMultiply', f'masked_ramp_{facet_index}')
            corrected_facet_mask.outValue >> masked_shade_ramp.input1
            shade_ramp.outColor >> masked_shade_ramp.input2

            self.color = masked_shade_ramp.outColor
        else:
            self.color = shade_ramp.outColor


class CollageShader(Network):
    relevant_context = ['object']
    delete = ['object']

    def __init__(self, context, obj, map_image_path):
        obj = obj.getTransform()
        obj_shape = obj.getShape()
        connections = listConnections(obj_shape, type='shadingEngine')
        if connections:
            old_sg = connections[0]
            for dsm in old_sg.dagSetMembers:
                connection = listConnections(dsm)[0]
                if connection.getShape() == obj_shape:
                    obj_shape.instObjGroups[0] // dsm
                    break
        
        map_dir_path = map_image_path.with_name(map_image_path.stem)
        map_data_path = map_dir_path / 'map data.json'
        with map_data_path.open() as file:
            facet_settings_dict = json.load(file)['facets']
        all_facet_settings = [facet_settings_dict[key] for key in sorted(facet_settings_dict.keys(), key=lambda x: int(x))]
        num_facets = len(all_facet_settings)
        multiple_facets = num_facets > 1

        if multiple_facets:
            surface_values_path = map_dir_path / 'surface values.json'
            masks_path = map_dir_path / 'masks'
            with surface_values_path.open() as file:
                surface_values = json.load(file)
            facet_centers = surface_values['facet centers']
            resolution = len(surface_values['blur values'])

        last_texture = None

        shader_color = None
        for facet_index in range(num_facets):
            facet_settings = all_facet_settings[facet_index]
            if multiple_facets:
                facet_center = facet_centers[facet_index]
            else:
                facet_center = [0, 0, 0]
            
            if not multiple_facets:
                masks_path = None
                resolution = None
            facet_shader = self.build(FacetShader(context | {'facet': str(facet_index)}, masks_path, resolution, obj, facet_index, facet_settings, facet_center), add_keys=False)
            
            if not multiple_facets:
                shader_color = facet_shader.color
                break

            if facet_index == 0:
                last_texture = self.utility('aiAdd', f'add_facets_0')
                facet_shader.color >> last_texture.input1
            elif facet_index > 1:
                new_texture = self.utility('aiAdd', f'add_facets_{facet_index - 1}')
                last_texture.outColor >> new_texture.input1
                last_texture = new_texture

            if facet_index >= 1:
                facet_shader.color >> last_texture.input2
        
        if not shader_color:
            if num_facets == 2:
                shader_color = last_texture.outColor
            else:
                shader_color = new_texture.outColor
        
        shader = self.shader('surfaceShader', 'collage_shader')
        shader_color >> shader.outColor

        sg = self.utility('shadingEngine', 'collage_shader_SG')
        shader.outColor >> sg.surfaceShader

        sets(sg, e=True, fe=obj)
        obj_shape.aiVisibleInDiffuseReflection.set(False)
