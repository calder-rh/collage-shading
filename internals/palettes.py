try:
    from internals.shading_path import shading_path
except:
    from shading_path import shading_path
from pathlib import Path
import json
import re
from abc import ABC, abstractmethod
from random import uniform
from enum import Enum
from os import walk


solid_region = 0.01
default_num_shades = 3
palette_regex = r'(\d+)(?!.*\.json).*'
shade_regex = r'[sS]\s*(\d+)(?!.*\.tx)(.*)'


def is_palette(path):
    path = Path(path)
    rel_path = path.relative_to(shading_path('palettes'))
    for part in rel_path.parts:
        if not re.fullmatch(palette_regex, part):
            return False
    return True


def is_valid_selection(path):
    path = Path(path)
    return is_palette(path) or (is_palette(path.parent) and re.fullmatch(shade_regex, path.name))


is_gradient = is_palette


def get_index(name):
    return int(re.fullmatch(palette_regex, name).group(1))


def shade_sort(name):
    match = re.fullmatch(shade_regex, name)
    return int(match.group(1)), match.group(2)
    

class FacetImage:
    def __init__(self, image, x, y, scale):
        self.image: str = image
        self.x: float = x - 0.5
        self.y: float = y - 0.5
        self.scale: float = scale


class Palette(ABC):
    def __init__(self, settings_path):
        self.settings_path = Path(settings_path)
    
    @staticmethod
    @abstractmethod
    def _instructions():
        ...

    def settings(self):
        if self.settings_path.exists():
            with open(self.settings_path) as file:
                return json.load(file)
        else:
            return self._default_settings()
    
    @abstractmethod
    def _default_shade_settings(self, **kwargs):
        ...
    
    def _default_settings(self, **kwargs):
        return {'up': 0, 'shades': self._default_shade_settings(**kwargs)}

    def make_settings_file(self, **kwargs):
        if self.settings_path.exists():
            return
        settings = self._default_settings(**kwargs)
        instructions = self._instructions()
        data = {'description': instructions} | settings
        with open(self.settings_path, 'w') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    @abstractmethod
    def make(self):
        ...
        
    
class ImagesPalette(Palette):
    def __init__(self, dir):
        self.dir = Path(dir)
        settings_path = self.dir / 'settings.json'
        self.images = [item for item in self.dir.iterdir() if item.is_file() and re.fullmatch(shade_regex, item.name)]
        self.images.sort(key = lambda item: shade_sort(item.name))
        super().__init__(settings_path)

    def _instructions(_):
        return {
            'filename prefix': 'What the filename of this shade file starts with',
            'up': 'The image will rotate so that this direction is pointing in the same direction as the object’s up vector. Measured clockwise from the top.',
            'shades': 'A list of all the shades that make up this palette, arranged from dark to light, with settings for each one. Here is a description of each setting:',
            'luminance': 'How much light should be hitting the surface to make this shade show up. Can be a list of two numbers indicating a region on the ramp to use for this shade. (Between 0 and 1)'
        }
        
    def _default_shade_settings(self):
        shade_settings = []
        num_shades = len(self.images)
        for i, image_file in enumerate(self.images):
            if num_shades == 1:
                ratio = 0.5
            else:
                ratio = i / (num_shades - 1)
            shade_number = re.fullmatch(shade_regex, image_file.name).group(1)
            shade_settings.append({'filename prefix': f's{shade_number}', 'luminance': ratio})
        return shade_settings
    
    def make(self, scale, edge_distance):
        settings = self.settings()
        horizontal_edge_distance, vertical_edge_distance = edge_distance

        self.facet_images = []
        self.luminance_values = []

        x = uniform(horizontal_edge_distance, 1 - horizontal_edge_distance)
        y = uniform(vertical_edge_distance, 1 - vertical_edge_distance)
        for setting in settings['shades']:
            image = [image for image in self.images if image.name.startswith(setting['filename prefix'])][0]
            self.facet_images.append(FacetImage(image, x, y, scale))
            luminance =  setting['luminance']
            if isinstance(luminance, list):
                self.luminance_values.append(luminance)
            else:
                luminance_start = luminance * (1 - solid_region)
                luminance_end = luminance_start + solid_region
                self.luminance_values.append([luminance_start, luminance_end])


class GradientPalette(Palette):
    def __init__(self, image):
        self.image = Path(image)
        index = get_index(self.image.name)
        settings_path = self.image.parent / f'{index} settings.json'
        super().__init__(settings_path)
    
    def _instructions(_):
        return {
            'up': 'The image will rotate so that this direction is pointing in the same direction as the object’s up vector. Measured clockwise from the top.',
            'shades': f'A list of all the parts of the gradient image that make up this palette, arranged from dark to light, with settings for each one. There are {default_num_shades} by default, but you can add or remove them. Here is a description of each setting:',
            'y': 'The y coordinate within the gradient image that is used for this shade. (0 = bottom, 1 = top, within the region allowed by the edge distance instructions.)',
            'luminance': 'How much light should be hitting the surface to make this shade show up. Can be a list of two numbers indicating a region on the ramp to use for this shade. (Between 0 and 1)'
        }
    
    def _default_shade_settings(self, num_shades=default_num_shades):
        shade_settings = []
        for i in range(num_shades):
            if num_shades == 1:
                ratio = 0.5
            else:
                ratio = i / (num_shades - 1)
            shade_settings.append({'luminance': ratio, 'y': ratio})
        return shade_settings
    
    def make(self, scale, edge_distance):
        settings = self.settings()
        horizontal_edge_distance, vertical_edge_distance = edge_distance

        self.facet_images = []
        self.luminance_values = []

        for setting in settings['shades']:
            x = uniform(horizontal_edge_distance, 1 - horizontal_edge_distance)
            y = vertical_edge_distance + setting['y'] * (1 - 2 * vertical_edge_distance)
            self.facet_images.append(FacetImage(self.image, x, y, scale))
            self.luminance_values.append(setting['luminance'])


def indices_to_path(indices):
    current_path = shading_path('palettes')
    for index in indices:
        next_path = None
        for item in current_path.iterdir():
            match = re.fullmatch(palette_regex, item.name)
            if not match:
                continue
            file_index = int(match.group(1))
            if file_index == index:
                next_path = item
                break
        if not next_path:
            raise Exception(f'There is no palette at a path corresponding to {indices}.')
        current_path = next_path
    return current_path


class PathType(Enum):
    invalid = 0
    palette = 1
    non_palette_directory = 2


def get_path_type(indices):
    try:
        path = indices_to_path(indices)
        if path.is_file() or any(item.is_file() and re.fullmatch(shade_regex, item.name) for item in path.iterdir()):
            return PathType.palette
        else:
            return PathType.non_palette_directory
    except:
        return PathType.invalid


def get_palette(input):
    if isinstance(input, list):
        path = indices_to_path(input)
    elif isinstance(input, str):
        path = shading_path(input)
    elif isinstance(input, Path):
        path = input
    else:
        raise Exception(f'Input to get_palette must be a string, Path object, or list of indices, not {input}')

    if path.is_dir():
        return ImagesPalette(path)
    elif re.fullmatch(shade_regex, path.name):
        return ImagesPalette(path.parent)
    else:
        return GradientPalette(path)


def ground_palette_path():
    ground_regex = r'(\d+).*ground!.*'
    current_path = shading_path('palettes')
    for root, dirs, _ in walk(current_path, topdown=False, followlinks=True):
        for dirname in dirs:
            if re.fullmatch(ground_regex, dirname):
                return Path(root, dirname)
    raise Exception('No ground palette found.')