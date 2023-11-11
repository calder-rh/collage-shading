import json
import numpy as np
from PIL import Image
from pathlib import Path
import sys
from math import floor


def make_blur_images(blur_values_path, map_data_path):
    masks_path = Path(blur_values_path).parent / 'masks'

    with open(blur_values_path) as file:
        blur_array = np.array(json.load(file)['blur values'])
    num_facets, resolution = blur_array.shape[:2]
    channel_arrays = (blur_array * 255).astype(np.uint8)

    expanded_channel_arrays = channel_arrays.copy()

    for py in range(resolution):
        for px in range(resolution):
            if np.array_equal(channel_arrays[:, py, px], [0] * num_facets):
                for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    nix = px + dx
                    niy = py + dy
                    if not ((0 <= nix < resolution) and (0 <= niy < resolution)):
                        continue
                    neighbor_blur_values = channel_arrays[:, niy, nix]
                    if not np.array_equal(neighbor_blur_values, [0] * num_facets):
                        expanded_channel_arrays[:, py, px] = neighbor_blur_values
                        break
    
    image_arrays = np.pad(expanded_channel_arrays.repeat(3).reshape(num_facets, resolution, resolution, 3), ((0, 0), (1, 1), (1, 1), (0, 0)), mode='edge')

    for i, facet in enumerate(image_arrays):
        image = Image.fromarray(facet)
        image.save(masks_path / f'{i}.png')


make_blur_images(sys.argv[1], sys.argv[2])
