import os
import time
from texture_atlas_packer import TextureAtlasPacker
from shape_generator import ShapeGenerator
import numpy as np

print('TEXTURE ATLAS PACKING DEMO\n')

#generate random shapes for packing
shape_gen = ShapeGenerator(42)
rectangles = shape_gen.generate_rectangles(20, 25, 200)
atlas_packer = TextureAtlasPacker(rectangles)

# sort textures based on area, perimeter, shortest side, or longest side
atlas_packer.sort_texture_dimensions("area")

# change atlas dimensions
atlas_packer.set_atlas_dimensions(512, 512)


print("\n------------------------ Running Greedy Packing Algorithm ------------------------\n")
start_time = time.perf_counter()
atlas_packer.pack("greedy")
end_time = time.perf_counter()
atlas_packer.visualize_atlas()
print(f"Execution time for greedy algorithm: {end_time-start_time}\n")

print("\n------------------------ Running Skyline Packing Algorithm ------------------------\n")
start_time = time.perf_counter()
atlas_packer.pack("skyline")
end_time = time.perf_counter()
atlas_packer.visualize_atlas()
print(f"Execution time for skyline algorithm: {end_time-start_time}\n")

print("\n------------------------ Running Guillotine Packing Algorithm ------------------------\n")
start_time = time.perf_counter()
atlas_packer.pack("guillotine")
end_time = time.perf_counter()
atlas_packer.visualize_atlas()
print(f"Execution time for guillotine algorithm: {end_time-start_time}\n")

print("\n------------------------ Running MaxRects Packing Algorithm ------------------------\n")
start_time = time.perf_counter()
atlas_packer.pack("maxrects")
end_time = time.perf_counter()
atlas_packer.visualize_atlas()
print(f"Execution time for maxrects algorithm: {end_time-start_time}\n")


# packing example using assets from folder TextureAssets1 (ignore)
'''
# 1. open folder containing practice textures and create a list of texture file names
folder_path = "TextureAssets1"
textures = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg'))]
print(f"Found {len(textures)} textures in the folder.")
print(f"Textures: {textures}")

# 2. Create a TextureAtlasPacker object with the textures 
atlas_packer = TextureAtlasPacker(textures, folder_path)
atlas_packer.get_texture_dimensions()
#print(atlas_packer.texture_dimensions)

# 3. Pack the textures into an atlas
atlas_packer.pack("greedy")
#print(f"Packing coordinates: {atlas_file}")

# 4. Visualize the packed atlas
atlas_packer.visualize_atlas()

'''