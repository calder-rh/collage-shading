from pymel.core import *
from internals.network import Network

from internals.global_controls import gcn
from internals.utilities import add_attr, connect_texture_placement
from internals.shading_path import shading_path
from internals.palettes import get_palette, build_palette_ramp, uv_input_builder_builder

from pathlib import Path

lighting_base_path = shading_path("ground lighting")


class GrassShader(Network):
    relevant_context = ["mesh"]

    def __init__(self, context, obj, palette_path):
        # Get the transform & shape nodes for the grass
        if obj.type() == "transform":
            obj_transform = obj
            obj_shape = obj.getShape()
        else:
            obj_transform = obj.getTransform()
            obj_shape = obj

        # File paths -----------------

        set_name = Path(str(obj.referenceFile() or system.sceneName())).stem
        obj_name = obj_transform.name(stripNamespace=True)
        base_dir = lighting_base_path / "base" / set_name
        base_dir.mkdir(parents=True, exist_ok=True)
        base_file = base_dir / (obj_name + ".exr")
        # self.scene_path = lighting_base_path / "scenes" /

        # Add attributes ------------------

        # Shader mode
        add_attr(
            obj_transform,
            ln="shader_mode",
            at="enum",
            enumName=["Preview", "Record", "Render"],
        )

        # Grass lighting
        add_attr(obj_transform, ln="base_lighting_weight", smn=0, smx=1, dv=1)
        add_attr(obj_transform, ln="scene_lighting_weight", smn=0, smx=1, dv=1)
        add_attr(obj_transform, ln="lighting_offset", smn=-1, smx=1, dv=0)
        add_attr(obj_transform, ln="max_luminance", min=0, smx=10, dv=1)

        # Grass shape
        add_attr(obj_transform, ln="grass_height", min=0, smx=200, dv=1)
        add_attr(obj_transform, ln="grass_density", min=0, smx=5, dv=4)
        # exponential: 4 becomes 10000 in aiNoise

        # Grass falloff
        add_attr(obj_transform, ln="grass_falloff", at="bool", dv=False)
        add_attr(obj_transform, ln="falloff_start", min=0, smx=5000, dv=1500)
        add_attr(obj_transform, ln="falloff_end", min=0, smx=5000, dv=2000)
        add_attr(obj_transform, ln="min_height_factor", min=0, max=1, dv=0)

        # Texture paths
        add_attr(obj_transform, ln="base_path", dt="string")
        obj_transform.base_path.set(str(base_file))
        add_attr(obj_transform, ln="scene_path", dt="string")

        # Create the shader ----------------

        # Luminance, live scene lighting

        luminance = self.utility("surfaceLuminance", "luminance")
        live_scene_lighting = self.divide(
            luminance.outValue, obj_transform.max_luminance, "live_scene_lighting"
        )

        live_lighting_grayscale = self.utility("blendColors", "live_lighting_grayscale")
        live_lighting_grayscale.color1.set(1, 1, 1)
        live_lighting_grayscale.color2.set(0, 0, 0)
        live_scene_lighting >> live_lighting_grayscale.blender

        # Recorded scene lighting

        recorded_scene_lighting = self.texture(
            "file", "recorded_scene_lighting", isColorManaged=True
        )
        obj_transform.scene_path >> recorded_scene_lighting.fileTextureName
        recorded_scene_lighting_tp = self.utility(
            "place2dTexture", f"recorded_scene_lighting_tp"
        )
        connect_texture_placement(recorded_scene_lighting_tp, recorded_scene_lighting)

        recorded_scene_lighting.useFrameExtension.set(True)
        SCENE.time1.outTime >> recorded_scene_lighting.frameExtension

        # Base lighting

        base_lighting = self.texture("file", "base_lighting", isColorManaged=True)
        obj_transform.base_path >> base_lighting.fileTextureName
        base_lighting_tp = self.utility("place2dTexture", f"base_lighting_tp")
        connect_texture_placement(base_lighting_tp, base_lighting)

        # Shader color value

        scene_lighting = self.utility("aiSwitch", "scene_lighting")
        obj_transform.shader_mode >> scene_lighting.attr("index")
        live_lighting_grayscale.output >> scene_lighting.input0
        recorded_scene_lighting.outColor >> scene_lighting.input2

        weighted_scene_lighting = self.multiply(
            scene_lighting.outColorR,
            obj_transform.scene_lighting_weight,
            "weighted_scene_lighting",
        )
        weighted_base_lighting = self.multiply(
            base_lighting.outColorR,
            obj_transform.base_lighting_weight,
            "weighted_base_lighting",
        )
        scene_plus_base = self.add(
            weighted_scene_lighting, weighted_base_lighting, "scene_plus_base"
        )
        final_lighting = self.add(
            scene_plus_base, obj_transform.lighting_offset, "final_lighting"
        )

        palette = get_palette(palette_path)
        palette.make(1, (0.5, 0.5))
        shade_ramp = build_palette_ramp(
            self, palette, "shade_ramp", final_lighting, uv_input_builder_builder(self)
        )

        atmosphere_blender = self.utility("blendColors", "atmosphere_blender")
        shade_ramp.outColor >> atmosphere_blender.color2
        gcn.atmospheric_perspective.color >> atmosphere_blender.color1
        gcn.ground_atmospheric_perspective >> atmosphere_blender.blender

        shader_color = self.utility("aiSwitch", "shader_color")
        obj_transform.shader_mode >> shader_color.attr("index")
        atmosphere_blender.output >> shader_color.input0
        live_lighting_grayscale.output >> shader_color.input1
        atmosphere_blender.output >> shader_color.input2

        # Shader displacement value

        grass_noise = self.utility("aiNoise", "grass_noise")
        grass_noise.coordSpace.set(3)
        grass_density = self.power(10, obj_transform.grass_density, "grass_density")
        grass_density >> grass_noise.scaleX
        grass_density >> grass_noise.scaleY
        grass_density >> grass_noise.scaleZ

        grass_point_height_without_falloff = grass_noise.outColorR

        grass_falloff = self.utility("remapValue", "falloff_amount")
        obj_transform.falloff_start >> grass_falloff.inputMin
        obj_transform.falloff_end >> grass_falloff.inputMax
        grass_falloff.outputMin.set(1)
        obj_transform.min_height_factor >> grass_falloff.outputMax
        SCENE.camera_distance.outFloat >> grass_falloff.inputValue

        grass_point_height_with_falloff = self.multiply(
            grass_point_height_without_falloff,
            grass_falloff.outValue,
            "grass_point_height_with_falloff",
        )

        grass_point_height = self.utility("floatCondition", "grass_point_height")
        obj_transform.grass_falloff >> grass_point_height.condition
        grass_point_height_with_falloff >> grass_point_height.floatA
        grass_point_height_without_falloff >> grass_point_height.floatB

        mode_is_render = self.utility("equal", "mode_is_render")
        mode_is_render.epsilon.set(0.5)
        obj_transform.shader_mode >> mode_is_render.input1
        mode_is_render.input2.set(2)

        displacement_amount = self.utility("floatCondition", "displacement_amount")
        mode_is_render.output >> displacement_amount.condition
        grass_point_height.outFloat >> displacement_amount.floatA
        displacement_amount.floatB.set(0)

        shader_displacement = self.shader("displacementShader", "shader_displacement")
        displacement_amount.outFloat >> shader_displacement.displacement
        obj_transform.grass_height >> shader_displacement.scale

        # Create the final shader

        sg = self.utility("shadingEngine", "grass_SG")
        shader = self.shader("surfaceShader", "grass_shader")
        shader_color.outColor >> shader.outColor
        shader.outColor >> sg.surfaceShader
        shader_displacement.displacement >> sg.displacementShader

        # Remove the object’s current shader

        connections = listConnections(obj_shape, type="shadingEngine")
        if connections:
            old_sg = connections[0]
            for dsm in old_sg.dagSetMembers:
                connection = listConnections(dsm)[0]
                if connection.getShape() == obj_shape:
                    if obj_shape.instObjGroups:
                        obj_shape.instObjGroups[0] // dsm
                        break

        # Apply the new shader

        sets(sg, e=True, fe=obj)

        # Set the render settings

        obj_shape.aiVisibleInDiffuseReflection.set(False)
        obj_shape.aiSelfShadows.set(False)
