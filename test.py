'''
import os
import time
from texture_atlas_packer import TextureAtlasPacker
from genetic_atlas_packer import GeneticAtlasPacker
from shape_generator import ShapeGenerator
import numpy as np

print('TEXTURE ATLAS PACKING DEMO\n')

#generate random shapes for packing
shape_gen = ShapeGenerator(42)
rectangles = shape_gen.generate_rectangles(20, 25, 200)
atlas_packer = TextureAtlasPacker(rectangles)

# sort textures based on area, perimeter, shortest side, or longest side
atlas_packer.sort_texture_dimensions("none")

# change atlas dimensions
atlas_packer.set_atlas_dimensions(512, 512)



print("\n------------------------ Running Greedy Packing Algorithm ------------------------\n")
start_time = time.perf_counter()
sp = atlas_packer.pack("greedy")
end_time = time.perf_counter()
#atlas_packer.visualize_atlas()
print(sp)
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



print("\n------------------------ Running Genetic Algorithm Packing ------------------------\n")
start_time = time.perf_counter()
genetic_packer = GeneticAtlasPacker(rectangles, seed = 42, atlas_height=512, atlas_width=512)
best_individual, best_fitness = genetic_packer.run()
genetic_packer.pack_best()
end_time = time.perf_counter()
genetic_packer.empty_space()
genetic_packer.visualize_atlas()
print(f"Execution time for genetic algorithm: {end_time-start_time}\n")

'''


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

import time
import random
from sys import maxsize
import numpy as np
from texture_atlas_packer import TextureAtlasPacker
from genetic_atlas_packer import GeneticAtlasPacker
from shape_generator import ShapeGenerator

# Benchmark Configuration
NUM_ITERATIONS = 10
ATLAS_WIDTH = 512
ATLAS_HEIGHT = 512
RANDOM_SEED = 42
RECT_NUMBER = 20
RECT_MIN_SIZE = 25
RECT_MAX_SIZE = 200

print(f"TEXTURE ATLAS PACKING BENCHMARK ({NUM_ITERATIONS} Iterations)\n")

random.seed(RANDOM_SEED)  # Set the random seed for reproducibility
seed_list = [random.randint(-maxsize-1, maxsize) for _ in range(NUM_ITERATIONS)]  # Generate a list of random seeds


standard_algorithms = ["greedy", "skyline", "guillotine", "maxrects"]
all_algorithms = standard_algorithms + ["genetic"]

# Tracking dictionaries for metrics
execution_times = {algo: [] for algo in all_algorithms}
empty_spaces = {algo: [] for algo in all_algorithms}

for iteration in range(1, NUM_ITERATIONS + 1):
    print(f"Running iteration {iteration}/{NUM_ITERATIONS}...")
    
    # Generate random rectangles once so every algorithm the same set
    shape_gen = ShapeGenerator(seed_list[iteration - 1])
    rectangles = shape_gen.generate_rectangles(RECT_NUMBER, RECT_MIN_SIZE, RECT_MAX_SIZE)

    # 1. Standard Texture Atlas Packer Algorithms
    for algo in standard_algorithms:
        atlas_packer = TextureAtlasPacker(rectangles)
        atlas_packer.sort_texture_dimensions("none")
        atlas_packer.set_atlas_dimensions(ATLAS_WIDTH, ATLAS_HEIGHT)

        start_time = time.perf_counter()
        empty_space = atlas_packer.pack(algo)
        end_time = time.perf_counter()

        execution_times[algo].append(end_time - start_time)
        empty_spaces[algo].append(empty_space)

    # 2. Genetic Atlas Packer Algorithm
    start_time = time.perf_counter()
    genetic_packer = GeneticAtlasPacker(
        rectangles, seed=42, atlas_height=ATLAS_HEIGHT, atlas_width=ATLAS_WIDTH
    )
    best_individual, best_fitness = genetic_packer.run()
    genetic_packer.pack_best()
    end_time = time.perf_counter()

    empty_space = genetic_packer.empty_space()

    execution_times["genetic"].append(end_time - start_time)
    empty_spaces["genetic"].append(empty_space)

# Final Averages Summary
print("\n" + "=" * 60)
print(f"{'Algorithm':<15} | {'Avg Exec Time (s)':<20} | {'Avg Empty Space':<15}")
print("=" * 60)

for algo in all_algorithms:
    avg_time = np.mean(execution_times[algo])
    avg_space = np.mean(empty_spaces[algo])
    print(f"{algo:<15} | {avg_time:<20.6f} | {avg_space:<15.2f}")

print("=" * 60)