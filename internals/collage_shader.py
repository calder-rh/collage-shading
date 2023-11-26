from pymel.core import *
from internals.network import Network
from internals import palettes
from internals.world_placement import RigidWorldPlacement
from internals.screen_placement import ScreenPlacement
from internals.tracking_projection import TrackingProjection
from internals.shading_controller import ShadingController
from internals.dialog_with_support import dialog_with_support
import json, re

noise_scale = 1000
noise_adjustment = 0.1


def error(title, message):
    dialog_with_support(title, message, ['I’ll fix it'], cb='I’ll fix it', db='I’ll fix it', icon='warning')
    exit()


class Luminance(Network):
    relevant_context = []
    delete = False

    def __init__(self, context):
        raw_luminance = self.utility('surfaceLuminance', 'raw_luminance')
        sc = ShadingController()
        facing_ratio = self.utility('aiFacingRatio', 'facing_ratio')

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

        adjusted_luminance = self.multiply(raw_luminance.outValue, sc.luminance_factor, 'adjusted_luminance')
        noisy_luminance = self.add(adjusted_luminance, adjusted_noise.outValue, 'noisy_luminance')
        
        remapped_facing_ratio = self.utility('remapValue', 'remapped_facing_ratio')
        remapped_facing_ratio.outputMin.set(0.6)
        remapped_facing_ratio.outputMax.set(0.05)
        facing_ratio.outValue >> remapped_facing_ratio.inputValue

        base_step_2nl = self.multiply(2, noisy_luminance, 'base_step_2nl')
        base = self.subtract(base_step_2nl, 1, 'base')
        abs_step_square = self.power(base, 2, 'abs_step_square')
        abs_base = self.power(abs_step_square, 0.5, 'abs_base')
        sign_base = self.divide(base, abs_base, 'sign_base')

        exponent_step_1_over_rfr = self.divide(1, remapped_facing_ratio.outValue, 'exponent_step_1_over_rfr')
        exponent = self.subtract(exponent_step_1_over_rfr, 1, 'exponent')

        power = self.power(abs_base, exponent, 'power')
        signed_power = self.multiply(sign_base, power, 'signed_power')

        signed_power_plus_1 = self.add(signed_power, 1, 'signed_power_plus_1')
        signed_power_plus_1_over_2 = self.divide(signed_power_plus_1, 2, 'signed_power_plus_1_over_2')

        self.luminance = signed_power_plus_1_over_2


class FacetShader(Network):
    relevant_context = ['object', 'facet']
    
    def __init__(self, context, masks_path, resolution, obj, facet_index, facet_settings, facet_center):
        multiple_facets = masks_path is not None

        palette = palettes.get_palette(facet_settings['palette'])
        palette.make(facet_settings['scale'], facet_settings['edge distance'])

        orienter_settings = facet_settings['orienter']
        if orienter_settings is None:
            world_placement = self.build(RigidWorldPlacement(context, obj, facet_center, facet_settings['object up']))

        else:
            if not objExists('facet_orienters'):
                error('No orienter group', 'Facet orienters must be in a group called facet_orienters')

            current_obj = PyNode('facet_orienters')
            for index, number in enumerate(orienter_settings):
                next_number_regex = '\D' + str(number) + '$'
                children = listRelatives(current_obj, children=True)
                matching_children = [child for child in children if re.search(next_number_regex, child.name())]
                num_matches = len(matching_children)
                if num_matches == 0:
                    error('Invalid orienter specification', f'There is no orienter matching {orienter_settings}.')
                if num_matches > 1:
                    error('Invalid orienter specification', f'There may be more than one orienter matching {orienter_settings}.')
                current_obj = matching_children[0]
                is_group = current_obj.getShape() is None
                if is_group != (index < len(orienter_settings) - 1):
                    error('Invalid orienter specification', f'The numbers {orienter_settings} do not match an orienter.')
            
            world_placement = self.build(RigidWorldPlacement(context, current_obj, (0, 0, 0), facet_settings['object up']))

        if (facet_up := facet_settings['image up']) is not None:
            image_up = facet_up
        else:
            image_up = palette.settings()['up']
        screen_placement = self.build(ScreenPlacement(context, world_placement, image_up))

        shade_ramp = self.utility('aiRampRgb', 'shade_ramp')
        setAttr(f'{shade_ramp.name()}.type', 0)
        self.build(Luminance({})).luminance >> shade_ramp.input

        for shade_index, (facet_image, luminance_value) in enumerate(zip(palette.facet_images, palette.luminance_values)):
            start_index = 2 * shade_index
            end_index = start_index + 1
            shade_ramp.ramp[start_index].ramp_Position.set(luminance_value[0])
            shade_ramp.ramp[end_index].ramp_Position.set(luminance_value[1])

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
