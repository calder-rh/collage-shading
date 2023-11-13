import numpy as np
from PIL import Image
from shading_path import shading_path
from math import atan2, degrees
import json
import sys
from pathlib import Path
from palettes import test_indices

gray = (127,) * 3
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
magenta = (255, 0, 255)
yellow = (255, 255, 0)
cyan = (0, 255, 255)
instruction_colors = [black, red, green, blue, magenta, yellow, cyan]

neighbor_coords = [(1, 0), (0, 1), (-1, 0), (0, -1)]


def error(msg):
    sys.stderr.write(msg)
    exit(1)


class FacetInstructions:
    def __init__(self, color_index, color):
        self.color_index = color_index
        self.color = color
        self.instruction_pixels = {color: set() for color in instruction_colors}

        self.palette_path_indices = None
        self.object_up = None
        self.image_up = None
        self.scale = None
        self.edge_distance = None
        self.blur_markers = None

    def error(self, msg):
        if self.color == white:
            error(f'Error in the region outside the facets\n{msg}')
        else:
            error(f'Error in the facet with color r={self.color[0]}, g={self.color[1]}, b={self.color[2]}\n{msg}')

    def add_instruction(self, color, coords):
        self.instruction_pixels[color].add(coords)
    
    def interpret_palette(self):
        locations = self.instruction_pixels[black]
        if not locations:
            return
        
        group_parents = {location: location for location in locations}
        for (y, x) in group_parents:
            for dy, dx in [(1, 0), (0, 1)]:
                ny = y + dy
                nx = x + dx
                if (ny, nx) in group_parents:
                    group_parents[(ny, nx)] = group_parents[(y, x)]

        group_representatives = {}
        for location in group_parents:
            last_parent = None
            this_parent = location
            while this_parent != last_parent:
                last_parent = this_parent
                this_parent = group_parents[this_parent]
            group_representatives[location] = this_parent
        
        groups = [[location for location in locations if group_representatives[location] == representative] for representative in set(group_representatives.values())]
        
        path_indices = [len(group) for group in sorted(groups, key = lambda group: sum([y + x for y, x in group]) / len(group))]
        if not test_indices(path_indices):
            self.error(f'There is no palette at a path corresponding to the indices {path_indices}.')
        self.palette_path_indices = path_indices
    
    def interpret_object_up(self):
        locations = self.instruction_pixels[blue]
        if not locations:
            return
        
        if len({y for y, _ in locations}) != 3:
            self.error('Invalid configuration of object up vector instructions (blue pixels). The instructions must be exactly 3 pixels tall.')
        
        top = None
        ou_neighbor_coords = [(1, 0), (2, 0)]
        ou_non_neighbor_coords = [(0, -1), (1, -1), (2, -1), (0, 1), (1, 1), (2, 1)]
        for y, x in locations:
            neighbors = {(y + dy, x + dx) for dy, dx in ou_neighbor_coords}
            if all(neighbor in locations for neighbor in neighbors) and not any(non_neighbor in locations for non_neighbor in ou_non_neighbor_coords):
                top = y, x
                break
        if top is None:
            self.error('Invalid configuration of object up vector instructions (blue pixels). There must be a vertical line of 3 blue pixels with no blue pixels touching it on the left or right.')
        top_y, top_x = top
        
        up_vector_coords = [0, 0, 0]
        for y, x in locations:
            if x == top_x:
                continue
            elif x > top_x:
                up_vector_coords[y - top_y] += 1
            else:
                up_vector_coords[y - top_y] -= 1

        norm = sum([coord ** 2 for coord in up_vector_coords]) ** 0.5
        if norm != 0:
            self.object_up = [coord / norm for coord in up_vector_coords]

    def interpret_image_up(self):
        locations = self.instruction_pixels[green]
        if not locations:
            return
        
        if len(locations) != 6:
            self.error('Invalid configuration of image up direction instructions (green pixels). There must be exactly 6 green pixels.')
        
        center = None
        for y, x in locations:
            neighbors = {(y + dy, x + dx) for dy, dx in neighbor_coords}
            if all(neighbor in locations for neighbor in neighbors):
                center = y, x
                break
        
        if not center:
            self.error('Invalid configuration of image up direction instructions (green pixels). There must be a green cross shape.')

        non_neighbor = (locations - neighbors - set((center,))).pop()
        self.image_up = 90 - degrees(atan2(center[0] - non_neighbor[0], non_neighbor[1] - center[1]))
    
    def interpret_scale(self):
        locations = self.instruction_pixels[red]
        if not locations:
            return
        
        lengths = [sum([y == row_y for y, _ in locations]) for row_y in sorted(list({location[0] for location in locations}))]
        if len(lengths) != 2:
            self.error('Invalid configuration of scale instructions (red pixels). There must be exactly 2 distinct y coordinates that have red pixels.')
        
        self.scale = lengths[0] / lengths[1]
    
    def interpret_edge_distance(self):
        locations = self.instruction_pixels[magenta]
        if not locations:
            return
        
        min_x = min(x for _, x in locations)
        max_x = max(x for _, x in locations)
        min_y = min(y for y, _ in locations)
        max_y = max(y for y, _ in locations)
        non_edge = [(y, x) for y, x in locations if x not in (min_x, max_x) and y not in (min_y, max_y)]
        if len(non_edge) != 1:
            self.error('Invalid configuration of edge distance instructions (magenta pixels). There must be a rectangle framed by a one-pixel-wide line, and exactly one pixel within that frame.')
        elif max_x - min_x < 3 or max_y - min_y < 3:
            self.error('Invalid configuration of edge distance instructions (magenta pixels). The frame must at least 4 pixels wide and tall.')
        y, x = non_edge[0]
        ratio_from_left = (x - min_x - 1) / (max_x - min_x - 2)
        ratio_from_top = (y - min_y - 1) / (max_y - min_y - 2)
        horizontal_edge_distance = min(ratio_from_left, 1 - ratio_from_left)
        vertical_edge_distance = min(ratio_from_top, 1 - ratio_from_top)
        self.edge_distance = [horizontal_edge_distance, vertical_edge_distance]
    
    def interpret_blur_markers(self):
        self.blur_markers = list(self.instruction_pixels[yellow])
    
    def interpret_instructions(self):
        self.interpret_palette()
        self.interpret_object_up()
        self.interpret_image_up()
        self.interpret_scale()
        self.interpret_edge_distance()
        self.interpret_blur_markers()


def make_map_data(image_path, data_path):
    image_path = Path(image_path)
    original_image = Image.open(image_path).convert('RGBA')
    image_on_white = Image.new('RGBA', original_image.size, 'WHITE')
    image_on_white.paste(original_image, (0, 0), original_image)
    image = np.asarray(image_on_white.convert('RGB'))

    height, width, _ = image.shape
    if height != width:
        error('The image must be square.')
    resolution = height

    if any(np.array_equal(pixel, gray) for pixel in image.reshape([1, -1, 3])[0]):
        error('It looks like you forgot to hide the UVs in the map image.')

    color_indices = {white: 0}
    color_counts = {white: 0}
    index_array = np.zeros((resolution, resolution), dtype=np.int8)
    instruction_pixels = {color: set() for color in instruction_colors}

    for y in range(resolution):
        for x in range(resolution):
            color = tuple(image[y, x].tolist())
            if color in instruction_colors:
                instruction_pixels[color].add((y, x))
                index_array[y][x] = -1 - instruction_colors.index(color)
            else:
                if color not in color_indices:
                    color_indices[color] = len(color_indices)
                    color_counts[color] = 0
                index_array[y][x] = color_indices[color]
                color_counts[color] += 1
            
    index_to_color = {index: color for color, index in color_indices.items()}
    all_facet_instructions = [FacetInstructions(index, index_to_color[index]) for index in range(len(color_indices))]
    
    for color, locations in instruction_pixels.items():
        this_color_index = -1 - instruction_colors.index(color)
        while locations:
            remaining_locations = set()
            for y, x in locations:
                neighbor_colors = set()
                for dx, dy in neighbor_coords:
                    nx = x + dx
                    ny = y + dy
                    if not ((0 <= nx < resolution) and (0 <= ny < resolution)):
                        continue
                    neighbor_colors.add(index_array[ny][nx])
                neighbor_colors.discard(this_color_index)
                if neighbor_colors & set(range(-len(instruction_colors), 0)):
                    error(f'Instructions touching each other at x={x}, y={y}.')
                num_neighbor_colors = len(neighbor_colors)
                if num_neighbor_colors == 0:
                    remaining_locations.add((y, x))
                elif num_neighbor_colors > 1:
                    error(f'Instruction color on facet border at x={x}, y={y}.')
                else:
                    neighbor_color_index = neighbor_colors.pop()
                    index_array[y][x] = neighbor_color_index
                    all_facet_instructions[neighbor_color_index].add_instruction(color, (y, x))
            locations = remaining_locations

    white_region = all_facet_instructions[0]
    white_region.interpret_instructions()
    white_palette_path_indices = white_region.palette_path_indices

    if len(all_facet_instructions) == 1:
        all_facet_instructions.append(all_facet_instructions[0])
        all_facet_instructions[-1].color_index = 1

    for facet in all_facet_instructions[1:]:
        facet.interpret_instructions()

        if facet.palette_path_indices is None:
            if white_palette_path_indices is None:
                error(f'No specified palette for region of color r={facet.color[0]}, g={facet.color[1]}, b={facet.color[2]}.')
            facet.palette_path_indices = white_palette_path_indices

        for attr_name, default_value in ('object_up', [0, 1, 0]), ('image_up', None), ('scale', 1), ('edge_distance', [0.1, 0.1]), ('blur_markers', []):
            if getattr(facet, attr_name) is None:
                white_value = getattr(white_region, attr_name)
                if white_value is not None:
                    setattr(facet, attr_name, white_value)
                else:
                    setattr(facet, attr_name, default_value)

    out_data = {}
    all_facet_instructions_data = {}
    for facet_instructions in all_facet_instructions[1:]:
        facet_instructions_data = {'palette': facet_instructions.palette_path_indices,
                                   'object up': facet_instructions.object_up,
                                   'image up': facet_instructions.image_up,
                                   'scale': facet_instructions.scale,
                                   'edge distance': facet_instructions.edge_distance,
                                   'blur markers': facet_instructions.blur_markers,
                                   'map color': facet_instructions.color}
        all_facet_instructions_data[facet_instructions.color_index] = facet_instructions_data
    out_data['facets'] = all_facet_instructions_data
    out_data['anti-aliasing warning'] = len(color_counts) > 30 or any(count < 25 for color, count in color_counts.items() if color != white)
    out_data['last modified'] = None
    if len(all_facet_instructions) > 2:
        out_data['pixels'] = index_array.tolist()

    with open(data_path, 'w') as file:
        json.dump(out_data, file, indent=4)


make_map_data(sys.argv[1], sys.argv[2])
