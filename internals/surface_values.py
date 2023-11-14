from pymel.core import *
from internals.coordinate_converter import CoordinateConverter
import json
import itertools
from internals.dialog_with_support import dialog_with_support

default_blur_size_ratio = 0.1


def vector_sum(p, q):
    return [pc + qc for pc, qc in zip(p, q)]


def calculate_surface_values(obj, map_data_path, blur_resolution):
    map_dir_path = map_data_path.parent
    surface_values_path = map_dir_path / 'surface values.json'
    masks_path = map_dir_path / 'masks'
    masks_exist = masks_path.exists() and any(file.suffix == '.png' for file in masks_path.iterdir())
    if masks_exist and surface_values_path.exists():
        return surface_values_path

    converter = CoordinateConverter({'object': obj.name()}, obj)

    with open(map_data_path) as file:
        map_data = json.load(file)

    facet_instructions = map_data['facets']
    pixels = map_data['pixels']
    map_resolution = len(pixels)

    pixel_xyzs = {tuple(pixel): converter.pixel_to_xyz(pixel[1], pixel[0], map_resolution) for pixel in itertools.chain.from_iterable(facet['blur markers'] for facet in facet_instructions.values())}

    try:
        marker_pairs = sorted([
            item + (
                sum(
                    ((xyzs := [pixel_xyzs[pixel] for pixel in item[:2]]) [0][c] 
                                                                - xyzs[1][c]) ** 2
                    for c in range(3)
                ) ** 0.5,
            )
            for item in
            itertools.chain.from_iterable([
                itertools.product(
                    *[
                        [tuple(blur_marker) for blur_marker in facet_instructions[facet_index]['blur markers']]
                        for facet_index in pair],
                    (pair,)
                )
                for pair in [
                    (str(index_1), str(index_2))
                    for index_1, index_2 in
                    itertools.combinations(
                        range(1, len(facet_instructions) + 1),
                        2
                    )
                ]
            ])],
            key=lambda item: item[3]
        )
    except TypeError:
        dialog_with_support('Error', 'Invalid configuration of blur distance markers (yellow pixels). These pixels must stay inside the UV shells.', ['I’ll fix it'], cb='I’ll fix it', db='I’ll fix it', icon='warning')
        exit()

    selected_pairs = []
    while marker_pairs:
        closest_pair = marker_pairs[0]
        selected_pairs.append(closest_pair)
        marker_pairs = marker_pairs[1:]
        used_markers = set(closest_pair[:2])
        marker_pairs = [mp for mp in marker_pairs if not used_markers & set(mp[:2])]

    defined_blur_sizes = {tuple(int(i) - 1 for i in mp[2]): mp[3] for mp in selected_pairs}

    blur_sizes = defined_blur_sizes.values()
    if len(blur_sizes) > 1:
        mean_blur_size = sum(blur_sizes) / len(defined_blur_sizes)
        max_blur_size = max(blur_sizes)
        one_size = False

        def get_blur_size(fi1, fi2):
            facet_pair = tuple(sorted((fi1, fi2)))
            if facet_pair in defined_blur_sizes:
                return defined_blur_sizes[facet_pair]
            else:
                return mean_blur_size
    elif blur_sizes:
        max_blur_size = list(blur_sizes)[0]
        one_size = True
    else:
        bounding_box = obj.getTransform().boundingBox()
        max_blur_size = (bounding_box.h ** 2 + bounding_box.w ** 2 + bounding_box.d) ** 0.5 * default_blur_size_ratio
        one_size = True
            
    def blur_samples(blur_size):
        blur_radius = blur_size / 2
        cube_coord = 0.35 * blur_radius
        octahedron_coord = 1 * blur_radius
        return [*itertools.product((-cube_coord, cube_coord), repeat=3)] + [[s if c == d else 0 for c in range(3)] for s in (-octahedron_coord, octahedron_coord) for d in range(3)]
    sample_contribution = 1 / (len(blur_samples(1)) + 1)

    num_facets = len(facet_instructions)
    blur_values = [[[0 for _ in range(blur_resolution)] for _ in range(blur_resolution)] for _ in range(num_facets)]
    facet_center_sums = [[[0, 0, 0], 0] for _ in range(num_facets)]

    progress_window = window(t='Generating mask images…')
    columnLayout()
    progress_control = progressBar(maxValue=blur_resolution, width=300)
    showWindow(progress_window)

    for py in range(blur_resolution):
        progressBar(progress_control, edit=True, pr=py)
        for px in range(blur_resolution):
            u, v = converter.pixel_to_uv(px, py, blur_resolution)
            center_xyz = converter.uv_to_xyz(u, v)

            # If it’s outside the UV shells, then we don’t need to do anything
            if center_xyz[0] is None:
                continue

            # Find the facet of the center point
            facet_px, facet_py = converter.uv_to_pixel(u, v, map_resolution)
            center_facet_index = pixels[facet_py][facet_px] - 1
            # Add this point to the sum of all the points in this facet
            facet_center_sum = facet_center_sums[center_facet_index]
            facet_center_sum[0] = vector_sum(facet_center_sum[0], center_xyz)
            facet_center_sum[1] += 1

            # A function that gets a dict of each facet that shows up in the samples of a given size, along with their counts
            def find_sample_facets(blur_size):
                sample_facet_counts = {center_facet_index: 1}
                for bs in blur_samples(blur_size):
                    sample_xyz = vector_sum(center_xyz, bs)
                    sample_px, sample_py = converter.xyz_to_pixel(sample_xyz, map_resolution)
                    sample_facet_index = pixels[sample_py][sample_px] - 1
                    if sample_facet_index not in sample_facet_counts:
                        sample_facet_counts[sample_facet_index] = 0
                    sample_facet_counts[sample_facet_index] += 1
                return sample_facet_counts
            
            # A function that takes these counts and calculates the blur values based on them
            def record_blur_contributions(sample_facets):
                for facet_index, count in sample_facets.items():
                    blur_values[facet_index][py][px] += sample_contribution * count

            # See which facets show up when using the maximum blur size
            maximum_blur_facet_counts = find_sample_facets(max_blur_size)
            
            # If there’s only one blur size, or there’s only one facet, then just go with this
            if one_size or len(maximum_blur_facet_counts) == 1:
                record_blur_contributions(maximum_blur_facet_counts)
                continue

            # Otherwise need to calculate the correct blur length for this context
            weighted_blur_sizes = [
                (get_blur_size(fi1, fi2), maximum_blur_facet_counts[fi1] * maximum_blur_facet_counts[fi2])
                for fi1, fi2 in 
                itertools.combinations(sorted(maximum_blur_facet_counts), 2)]
            
            blur_size = sum(size * weight for size, weight in weighted_blur_sizes) / sum(weight for _, weight in weighted_blur_sizes)

            record_blur_contributions(find_sample_facets(blur_size))
    
    facet_centers = [[c / count for c in total] for total, count in facet_center_sums]

    data = {}
    data['facet centers'] = facet_centers
    data['blur values'] = blur_values

    if not masks_path.exists():
        masks_path.mkdir()
    with surface_values_path.open(mode='w') as file:
        json.dump(data, file)
    
    deleteUI(progress_window)
    converter.destroy()

    return surface_values_path
