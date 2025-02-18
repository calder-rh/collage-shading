from pymel.core import *
from internals.network import Network

from internals.utilities import set_visibility_in_render, add_attr


class LightingSets(Network):
    relevant_context = []
    prefix = ""
    delete = False

    def __init__(self, _):
        self.global_set = self.make(sets, "lighting_sets", em=True)

        self.illuminees = self.make(sets, "illuminees", em=True)
        self.ground_meshes = self.make(sets, "ground_meshes", em=True)
        self.default_lights = self.make(sets, "default_lights", em=True)
        self.added_lights_sets = self.make(sets, "added_lights_sets", em=True)
        self.excluded_lights_sets = self.make(sets, "excluded_lights_sets", em=True)

        sets(self.global_set, add=self.illuminees)
        sets(self.global_set, add=self.default_lights)
        sets(self.global_set, add=self.added_lights_sets)
        sets(self.global_set, add=self.excluded_lights_sets)

    def add_light(self, light):
        sets(self.default_lights, add=light)

    def remove_light(self, light):
        sets(self.default_lights, remove=light)


lighting_sets = LightingSets({})


class SunPairShaders(Network):
    relevant_context = []
    prefix = ""
    delete = False

    def __init__(self, _):
        sun_shader = self.shader("surfaceShader", "sun_shader")
        sun_shader.outColor.set((1, 1, 1))
        self.sun_sg = self.utility("shadingEngine", "sun_SG")
        sun_shader.outColor >> self.sun_sg.surfaceShader


class GlobalControls(Network):
    relevant_context = []
    prefix = ""
    delete = False

    node_name = "shading_controls"

    def __init__(self, _):
        is_new = not objExists(self.node_name)

        if is_new:
            lighting_controller_trans, _ = self.poly(
                polyCube, self.node_name, w=20, h=20, d=20
            )
            setAttr(lighting_controller_trans.r, l=True)
            lighting_controller_shape = lighting_controller_trans.getShape()
            set_visibility_in_render(lighting_controller_shape, False)
            delete(lighting_controller_trans, ch=True)

            light_direction_cone_trans, _ = self.poly(
                polyCone,
                "light_direction_cone",
                radius=8,
                height=80,
                heightBaseline=-1,
                axis=(0, 1, 0),
            )
            light_source_ball_trans, _ = self.poly(
                polySphere, "light_source_ball", radius=4, axis=(0, 1, 0)
            )
            light_source_ball_trans.ty.set(78)
            self.light_direction_trans, _ = polyUnite(
                light_direction_cone_trans, light_source_ball_trans, n="light_direction"
            )
            light_direction_shape = self.light_direction_trans.getShape()
            delete(self.light_direction_trans, ch=True)

            initial_sg_connection = listConnections(
                light_direction_shape, s=False, c=True, p=True
            )[0]
            initial_sg_connection[0] // initial_sg_connection[1]
            sun_sg = SunPairShaders({}).sun_sg
            sets(sun_sg, e=True, fe=light_direction_shape)
            parent(self.light_direction_trans, lighting_controller_trans)
            setAttr(self.light_direction_trans.t, l=True)
            setAttr(self.light_direction_trans.s, l=True)
            set_visibility_in_render(light_direction_shape, False)

            gcn = lighting_controller_trans
            addAttr(gcn, ln="default_lightness", smn=0, smx=1, dv=0.5)
            addAttr(gcn, ln="default_contrast", min=0, smx=1, dv=0.24)

            addAttr(gcn, ln="ground_luminance_weight", min=0, smx=1, dv=0.35)
            addAttr(gcn, ln="ground_light_offset", smn=-1, smx=1, dv=0)

            addAttr(gcn, ln="atmospheric_perspective", at="compound", nc=5)
            addAttr(gcn, p="atmospheric_perspective", ln="enable", at="bool", dv=True)
            addAttr(
                gcn,
                p="atmospheric_perspective",
                ln="min_distance",
                min=0,
                smx=2000,
                dv=1000,
            )
            addAttr(
                gcn,
                p="atmospheric_perspective",
                ln="half_distance",
                min=1,
                smx=2000,
                dv=800,
            )
            addAttr(
                gcn,
                p="atmospheric_perspective",
                ln="ground_half_distance",
                min=1,
                smx=2000,
                dv=800,
            )
            addAttr(gcn, p="atmospheric_perspective", ln="color", at="float3", uac=True)
            addAttr(gcn, ln="colorR", at="float", parent="color")
            addAttr(gcn, ln="colorG", at="float", parent="color")
            addAttr(gcn, ln="colorB", at="float", parent="color")
            lighting_controller_trans.atmospheric_perspective.color.set(
                0.119, 0.294, 0.358
            )

            addAttr(gcn, ln="noise_frequency", min=1, smx=2000, dv=2000)
            addAttr(gcn, ln="noise_strength", min=0, max=1, dv=0.1)

            addAttr(gcn, ln="texture_scale", min=0, smx=1000, dv=500)

            # addAttr(gcn, ln="bands", at="compound", nc=4)
            # addAttr(gcn, p="bands", ln="band_spacing", dv=200)
            # addAttr(gcn, p="bands", ln="band_count", at="short", dv=20)
            # addAttr(gcn, p="bands", ln="initial_band_offset", dv=0)
            # addAttr(gcn, p="bands", ln="band_offset")

            add_attr(gcn, ln="bands", at="compound", nc=4)
            add_attr(gcn, p="bands", ln="band_spacing", dv=200)
            add_attr(gcn, p="bands", ln="band_count", at="short", dv=20)
            add_attr(gcn, p="bands", ln="initial_band_offset", dv=0)
            add_attr(gcn, p="bands", ln="band_offset")

            addAttr(gcn, ln="camera", at="compound", nc=8)
            addAttr(gcn, p="camera", ln="camera_message", at="message")
            addAttr(gcn, p="camera", ln="world_matrix", at="matrix")
            addAttr(gcn, p="camera", ln="camera_position", at="float3")
            addAttr(gcn, ln="camera_position_x", at="float", p="camera_position")
            addAttr(gcn, ln="camera_position_y", at="float", p="camera_position")
            addAttr(gcn, ln="camera_position_z", at="float", p="camera_position")
            addAttr(gcn, p="camera", ln="inverse_world_matrix", at="matrix")
            addAttr(gcn, p="camera", ln="focal_length", dv=35)
            addAttr(gcn, p="camera", ln="horizontal_aperture", dv=1.417)
            addAttr(gcn, p="camera", ln="aspect_ratio")
            addAttr(gcn, p="camera", ln="focal_length_factor")

            addAttr(gcn, ln="other_internals", at="compound", nc=6)
            addAttr(gcn, p="other_internals", ln="luminance")
            addAttr(gcn, p="other_internals", ln="noise")
            addAttr(gcn, p="other_internals", ln="camera_direction_vector", at="float3")
            addAttr(
                gcn,
                ln="camera_direction_vector_x",
                at="float",
                p="camera_direction_vector",
            )
            addAttr(
                gcn,
                ln="camera_direction_vector_y",
                at="float",
                p="camera_direction_vector",
            )
            addAttr(
                gcn,
                ln="camera_direction_vector_z",
                at="float",
                p="camera_direction_vector",
            )
            addAttr(gcn, p="other_internals", ln="light_direction_vector", at="float3")
            addAttr(
                gcn,
                ln="light_direction_vector_x",
                at="float",
                p="light_direction_vector",
            )
            addAttr(
                gcn,
                ln="light_direction_vector_y",
                at="float",
                p="light_direction_vector",
            )
            addAttr(
                gcn,
                ln="light_direction_vector_z",
                at="float",
                p="light_direction_vector",
            )
            addAttr(gcn, ln="light_dot", at="float", p="other_internals")
            addAttr(gcn, ln="ground_atmospheric_perspective", p="other_internals")

            # Find the luminance

            luminance = self.utility("surfaceLuminance", "luminance")
            centered_luminance = self.subtract(
                luminance.outValue, 0.5, "centered_luminance"
            )
            remapped_luminance = self.multiply(
                centered_luminance, 2, "remapped_luminance"
            )
            remapped_luminance >> gcn.other_internals.luminance

            camera_decomposer = self.utility("decomposeMatrix", "camera_decomposer")
            gcn.camera.world_matrix >> camera_decomposer.inputMatrix

            # Calculate the camera and light direction vectors

            camera_rotation_matrix = self.utility(
                "composeMatrix", "camera_rotation_matrix"
            )
            camera_decomposer.outputRotate >> camera_rotation_matrix.inputRotate
            move_1_z = self.utility("composeMatrix", "move_1_z")
            move_1_z.inputTranslateZ.set(1)
            move_1_in_camera_direction = self.utility(
                "multMatrix", "move_1_in_camera_direction"
            )
            move_1_z.outputMatrix >> move_1_in_camera_direction.matrixIn[0]
            (
                camera_rotation_matrix.outputMatrix
                >> move_1_in_camera_direction.matrixIn[1]
            )
            camera_rotation_calculator = self.utility(
                "decomposeMatrix", "camera_rotation_calculator"
            )
            (
                move_1_in_camera_direction.matrixSum
                >> camera_rotation_calculator.inputMatrix
            )
            (
                camera_rotation_calculator.outputTranslate
                >> gcn.other_internals.camera_direction_vector
            )

            decompose_light = self.utility("decomposeMatrix", "decompose_light")
            self.light_direction_trans.worldMatrix[0] >> decompose_light.inputMatrix
            light_rotation_matrix = self.utility(
                "composeMatrix", "light_rotation_matrix"
            )
            decompose_light.outputRotate >> light_rotation_matrix.inputRotate
            move_1_z = self.utility("composeMatrix", "move_1_z")
            move_1_z.inputTranslateZ.set(1)
            move_1_in_light_direction = self.utility(
                "multMatrix", "move_1_in_light_direction"
            )
            move_1_z.outputMatrix >> move_1_in_light_direction.matrixIn[0]
            light_rotation_matrix.outputMatrix >> move_1_in_light_direction.matrixIn[1]
            light_rotation_calculator = self.utility(
                "decomposeMatrix", "light_rotation_calculator"
            )
            move_1_in_light_direction.matrixSum >> light_rotation_calculator.inputMatrix
            (
                light_rotation_calculator.outputTranslate
                >> gcn.other_internals.light_direction_vector
            )

            # Calculate the camera position

            camera_decomposer.outputTranslate >> gcn.camera.camera_position

            global_sampler_info = self.utility("samplerInfo", "global_sampler_info")

            # Calculate the global surface normal and dot with light direction

            transposed_camera = self.utility("transposeMatrix", "transposed_camera")
            camera_rotation_matrix.outputMatrix >> transposed_camera.inputMatrix
            normal_components = []
            for i in range(3):
                row = self.utility("pointMatrixMult", f"camera_row_{i + 1}")
                transposed_camera.outputMatrix >> row.inMatrix
                vector = [0, 0, 0]
                vector[i] = 1
                row.inPoint.set(vector)
                component = self.utility("aiDot", f"normal_component_{i + 1}")
                row.output >> component.input1
                global_sampler_info.normalCamera >> component.input2
                normal_components.append(component)
            light_dot = self.utility("aiDot", "light_dot")
            gcn.other_internals.light_direction_vector >> light_dot.input1
            for component, attr_axis in zip(normal_components, "XYZ"):
                component.outValue >> light_dot.attr("input2" + attr_axis)
            light_dot.outValue >> gcn.other_internals.light_dot

            # Calculate the atmospheric perspective for ground meshes

            dx = self.subtract(
                gcn.camera_position_x,
                global_sampler_info.pointWorldX,
                "camera_point_dx",
            )
            dy = self.subtract(
                gcn.camera_position_y,
                global_sampler_info.pointWorldY,
                "camera_point_dy",
            )
            dz = self.subtract(
                gcn.camera_position_z,
                global_sampler_info.pointWorldZ,
                "camera_point_dz",
            )
            dx2 = self.power(dx, 2, "camera_point_dx_2")
            dy2 = self.power(dy, 2, "camera_point_dy_2")
            dz2 = self.power(dz, 2, "camera_point_dz_2")
            sum_1 = self.add(dx2, dy2, "dx2_plus_dy2")
            sum_2 = self.add(sum_1, dz2, "sum_of_squared_dxyz")
            camera_distance = self.power(sum_2, 0.5, "camera_distance")
            offset_camera_distance = self.subtract(
                camera_distance, gcn.min_distance, "offset_camera_distance"
            )

            num_half_distances = self.divide(
                offset_camera_distance, gcn.ground_half_distance, "num_half_distances"
            )
            original_color_remaining = self.power(
                0.9, num_half_distances, "original_color_remaining"
            )
            atmosphere_color_amount = self.subtract(
                1, original_color_remaining, "atmosphere_color_amount"
            )
            atmospheric_perspective_amount = self.multiply(
                atmosphere_color_amount, gcn.enable, "atmospheric_perspective_amount"
            )
            atmospheric_perspective_amount >> gcn.ground_atmospheric_perspective

            # Calculate the aspect ratio

            res = SCENE.defaultResolution
            aspect_ratio = self.divide(res.width, res.height, "aspect_ratio")
            aspect_ratio >> gcn.aspect_ratio

            # Calculate the focal length factor

            millimeters_per_inch = 25.4
            attrs = ["focal_length", "horizontal_aperture", "focal_length_factor"]
            expr = f"focal_length_factor = focal_length / (horizontal_aperture * {millimeters_per_inch});"
            node = self.expression("focal_length_factor", attrs, expr)
            gcn.camera.horizontal_aperture >> node.horizontal_aperture
            gcn.camera.focal_length >> node.focal_length
            node.focal_length_factor >> gcn.focal_length_factor

            # Calculate the global noise

            noise = self.utility("aiNoise", "value_noise")
            noise.coordSpace.set(3)
            noise_x_frequency = self.multiply(
                gcn.noise_frequency, gcn.camera.aspect_ratio, "noise_x_frequency"
            )
            noise_x_frequency >> noise.scale.scaleX
            gcn.noise_frequency >> noise.scale.scaleY
            gcn.noise_frequency >> noise.scale.scaleZ

            noise_projection = self.utility("projection", "noise_projection")
            noise_projection.projType.set(8)
            gcn.camera.camera_message >> noise_projection.linkedCamera
            noise.outColor >> noise_projection.image

            noise_remap = self.utility("remapValue", "noise_remap")
            noise_projection.outColor.outColorR >> noise_remap.inputValue
            noise_min = self.multiply(gcn.noise_strength, -1, "noise_min")
            noise_min >> noise_remap.outputMin
            gcn.noise_strength >> noise_remap.outputMax

            noise_remap.outValue >> gcn.noise

            self.node = gcn
        else:
            self.node = PyNode(self.node_name)

    def connect_camera(self, camera):
        camera_transform = camera.getTransform()
        camera_shape = camera.getShape()

        camera_shape.message >> self.node.camera.camera_message
        camera_transform.worldMatrix[0] >> self.node.camera.world_matrix
        camera_transform.worldInverseMatrix[0] >> self.node.camera.inverse_world_matrix
        camera_shape.focalLength >> self.node.camera.focal_length
        camera_shape.horizontalFilmAperture >> self.node.camera.horizontal_aperture

    def disconnect_camera(self):
        for attr in [
            self.node.camera.camera_message,
            self.node.camera.world_matrix,
            self.node.camera.inverse_world_matrix,
            self.node.camera.focal_length,
            self.node.camera.horizontal_aperture,
        ]:
            connections = listConnections(
                attr, source=True, destination=False, plugs=True
            )
            if connections:
                connections[0] // attr

    def reload(self): ...


global_controls = GlobalControls({})
gcn = global_controls.node
