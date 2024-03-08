from pymel.core import *
from internals.network import Network
from internals import palettes
from internals.world_placement import WorldPlacement
from internals.screen_placement import CalculatedScreenPlacement
from internals.tracking_projection import TrackingProjection
from internals.dialog_with_support import dialog_with_support
from internals.unique_name import format_unique_name
from internals.global_controls import gcn
import json, re


def error(title, message):
    dialog_with_support(title, message, ['I’ll fix it'], cb='I’ll fix it', db='I’ll fix it', icon='warning')
    exit()


class FacetShader(Network):
    relevant_context = ['mesh', 'facet']
    
    def __init__(self, context, masks_path, resolution, obj, lightness, facet_index, facet_settings, facet_center, orienter_group_name, orienter_transform_path):
        multiple_facets = masks_path is not None

        orienter_transforms = None
        if orienter_transform_path.exists():
            with orienter_transform_path.open() as file:
                orienter_transforms = json.load(file)

        palette = palettes.get_palette(facet_settings['palette'])
        palette.make(facet_settings['scale'], facet_settings['edge distance'])

        orienter_settings = facet_settings['orienter']
        obj_up_settings = facet_settings['object up']

        if obj.type() == 'transform':
            obj_shape = obj.getShape()
        else:
            obj_shape = obj

        if orienter_settings is None:
            if obj_up_settings is None:
                obj_up_settings = (0, 1, 0)
            world_placement = self.build(WorldPlacement(context, obj, facet_center, obj_up_settings))

        else:
            if obj_up_settings is None:
                obj_up_settings = (0, 1, 0)
            
            if objExists(orienter_group_name):
                orienter_group = PyNode(orienter_group_name)
            else:
                orienter_group = group(name=orienter_group_name, em=True)

            u, v, angle = orienter_settings
            pin = createNode('uvPin', name=f'facet_{facet_index}_pin')
            pin.coordinate[0].set([u, v])
            pin.normalAxis.set(2)
            pin.tangentAxis.set(0)
            mesh = obj_shape.worldMesh[0]
            mesh >> pin.originalGeometry
            mesh >> pin.deformedGeometry
            locator_shape = createNode('locator', name=f'facet_{facet_index}_locator')
            locator_transform = locator_shape.getTransform()
            locator_transform.rename(name=f'facet_{facet_index}')
            pin.outputMatrix[0] >> locator_transform.offsetParentMatrix

            if orienter_transforms:
                locator_transform.t.set(orienter_transforms[str(facet_index)]['translate'])
                locator_transform.r.set(orienter_transforms[str(facet_index)]['rotate'])
                locator_transform.s.set(orienter_transforms[str(facet_index)]['scale'])
            else:
                locator_transform.rz.set(angle)

            parent(locator_transform, orienter_group)

            world_placement = self.build(WorldPlacement(context, locator_transform, (0, 0, 0), obj_up_settings))

        if (facet_up := facet_settings['image up']) is not None:
            image_up = facet_up
        else:
            image_up = palette.settings()['up']
        screen_placement = self.build(CalculatedScreenPlacement(context, world_placement, image_up))

        shade_ramp = self.utility('aiRampRgb', 'shade_ramp')
        shade_ramp.attr('type').set(0)
        lightness >> shade_ramp.input

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
    relevant_context = ['mesh']
    delete = ['mesh']

    def __init__(self, context, obj, map_image_path):
        obj = obj.getTransform()
        obj_shape = obj.getShape()
        connections = listConnections(obj_shape, type='shadingEngine')
        if connections:
            old_sg = connections[0]
            for dsm in old_sg.dagSetMembers:
                connection = listConnections(dsm)[0]
                if connection.getShape() == obj_shape:
                    if obj_shape.instObjGroups:
                        obj_shape.instObjGroups[0] // dsm
                        break

        map_dir_path = map_image_path.with_name(map_image_path.stem)

        self.orienter_group_name = format_unique_name(obj) + '_orienters'
        orienter_transform_path = map_dir_path / 'orienters.json'

        if objExists(self.orienter_group_name):
            orienter_transform_values = {}
            for orienter in listRelatives(self.orienter_group_name):
                if (match := re.fullmatch(r'facet_(\d+)', orienter.name())):
                    facet_num = match.group(1)
                    orienter_transform_values[facet_num] = {'translate': list(orienter.t.get()), 'rotate': list(orienter.r.get()), 'scale': list(orienter.s.get())}
            with orienter_transform_path.open('w') as file:
                json.dump(orienter_transform_values, file, indent=4)
            
            delete(self.orienter_group_name)
        else:
            if orienter_transform_path.exists():
                orienter_transform_path.unlink()
        
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



        if not obj_shape.hasAttr('lightness'):
            addAttr(obj_shape, ln='lightness')
            gcn.default_lightness >> obj_shape.lightness

        if not obj_shape.hasAttr('saturation'):
            addAttr(obj_shape, ln='saturation')
            obj_shape.saturation.set(1)


        last_texture = None
        raw_color = None
        for facet_index in range(num_facets):
            facet_settings = all_facet_settings[facet_index]
            if multiple_facets:
                facet_center = facet_centers[facet_index]
            else:
                facet_center = [0, 0, 0]
            
            if not multiple_facets:
                masks_path = None
                resolution = None
            facet_shader = self.build(FacetShader(context | {'facet': str(facet_index)}, masks_path, resolution, obj, obj_shape.lightness, facet_index, facet_settings, facet_center, self.orienter_group_name, orienter_transform_path), add_keys=False)
            
            if not multiple_facets:
                raw_color = facet_shader.color
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
        
        if not raw_color:
            if num_facets == 2:
                raw_color = last_texture.outColor
            else:
                raw_color = new_texture.outColor
    
        # Desaturate the back

        desaturator = self.utility('remapHsv', 'desaturator')
        raw_color >> desaturator.color
        obj_shape.saturation >> desaturator.saturation[1].saturation_FloatValue
        
        shader = self.shader('surfaceShader', 'collage_shader')
        desaturator.color >> shader.outColor

        sg = self.utility('shadingEngine', 'collage_shader_SG')
        shader.outColor >> sg.surfaceShader

        sets(sg, e=True, fe=obj)
        obj_shape.aiVisibleInDiffuseReflection.set(False)
        obj_shape.aiSelfShadows.set(False)
