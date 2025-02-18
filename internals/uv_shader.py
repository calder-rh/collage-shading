from pymel.core import *
from internals.network import Network

from internals.global_controls import gcn
from internals.utilities import connect_texture_placement, do_later, add_attr
from internals.palettes import get_palette, build_palette_ramp, uv_input_builder_builder


class UVShader(Network):
    relevant_context = ["mesh"]
    delete = ["mesh"]

    def __init__(self, context, obj, palette_path):
        if obj.type() == "transform":
            obj_transform = obj
            obj_shape = obj.getShape()
        else:
            obj_transform = obj.getTransform()
            obj_shape = obj

        connections = listConnections(obj_shape, type="shadingEngine")
        if connections:
            old_sg = connections[0]
            for dsm in old_sg.dagSetMembers:
                connection = listConnections(dsm)[0]
                if connection.getShape() == obj_shape:
                    if obj_shape.instObjGroups:
                        obj_shape.instObjGroups[0] // dsm
                        break

        # Add user customizable attributes
        add_attr(obj_transform, ln="luminance_weight", min=0, smx=1, dv=0.5)
        add_attr(obj_transform, ln="light_offset", smn=0, smx=1, dv=0)
        gcn.ground_luminance_weight >> obj_transform.luminance_weight
        gcn.ground_light_offset >> obj_transform.light_offset

        add_attr(obj_transform, ln="angle_remap", at="message")

        # Make this treated as an illuminee
        add_attr(obj_transform, ln="internals", at="compound", nc=5)
        add_attr(
            obj_transform, p="internals", ln="used_as_illuminee", at="bool", dv=True
        )
        add_attr(
            obj_transform, p="internals", ln="regular_illuminee", at="bool", dv=False
        )
        add_attr(obj_transform, p="internals", ln="lightness")
        add_attr(obj_transform, p="internals", ln="added_lights", at="message")
        add_attr(obj_transform, p="internals", ln="excluded_lights", at="message")

        palette = get_palette(palette_path)
        palette.make(1, (0, 0))

        shade_ramp = build_palette_ramp(
            self,
            palette,
            "shade_ramp",
            obj_transform.lightness,
            uv_input_builder_builder(self),
        )

        # Apply atmospheric perspective

        atmosphere_blender = self.utility("blendColors", "atmosphere_blender")
        shade_ramp.outColor >> atmosphere_blender.color2
        gcn.atmospheric_perspective.color >> atmosphere_blender.color1
        gcn.ground_atmospheric_perspective >> atmosphere_blender.blender

        shader = self.shader("surfaceShader", "collage_shader")
        atmosphere_blender.output >> shader.outColor

        sg = self.utility("shadingEngine", "collage_shader_SG")
        shader.outColor >> sg.surfaceShader

        sets(sg, e=True, fe=obj)
        obj_shape.aiVisibleInDiffuseReflection.set(False)
        obj_shape.aiSelfShadows.set(False)

        # Calculate the lightness

        light_dot_remap = self.utility("remapValue", "light_dot_remap")
        light_dot_remap.inputMin.set(-1)
        gcn.other_internals.light_dot >> light_dot_remap.inputValue
        light_dot_remap.message >> obj_transform.angle_remap

        weighted_luminance = self.multiply(
            gcn.luminance, obj_transform.luminance_weight, "weighted_luminance"
        )
        sum_luminance = self.add(
            light_dot_remap.outValue, weighted_luminance, "sum_luminance"
        )
        lightness = self.add(sum_luminance, obj_transform.light_offset, "lightness")
        lightness >> obj_transform.lightness
