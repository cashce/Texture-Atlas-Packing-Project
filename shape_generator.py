import random

# generate shapes for testing packing algorithms
class ShapeGenerator:

    def __init__(self, random_seed):
        self.random_seed = random_seed
        random.seed(random_seed)
        self.shapes = dict()

    # generates a list of squares with random size
    def generate_squares(self, num_shapes, min_size, max_size):
        for i in range(num_shapes):
            width = random.randint(min_size, max_size)
            height = width
            area = width * height
            rgb = self.get_random_rgb()
            self.shapes[f'square{i}'] = (height, width, area, rgb)
        return self.shapes

    # generates a list of rectangles with random width and height
    def generate_rectangles(self, num_shapes, min_size, max_size):
        for i in range(num_shapes):
            width = random.randint(min_size, max_size)
            height = random.randint(min_size, max_size)
            area = width * height
            rgb = self.get_random_rgb()
            self.shapes[f'rect{i}'] = (height, width, area, rgb)
        return self.shapes

    # TODO: implement later 
    def generate_rectilinear_shapes(self, num_shapes, min_size, max_size):
        pass

    def get_random_rgb(self):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return (r, g, b)