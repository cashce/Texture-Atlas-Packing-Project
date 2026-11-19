import os
import manual_unpacker
from genetic_atlas_packer import GeneticAtlasPacker
from matplotlib import pyplot as plt
import numpy as np


def is_dir_empty_fast(dir_path):
    try:
        with os.scandir(dir_path) as entries:
            # any() will return True as soon as it finds the first entry
            return not any(entries)
    except FileNotFoundError:
        return False  # Handle case where directory doesn't exist

folder_path = "PackedTexture"
packed_texture = folder_path + "/Vampire.png"
if is_dir_empty_fast("UnpackedTextures"):
    results=manual_unpacker.unpack_atlas(packed_texture, "UnpackedTextures", min_area=10)
else:
    for filename in os.listdir("UnpackedTextures"):
        # Construct full file path
        file_path = os.path.join("UnpackedTextures", filename)
    
        # Ensure it's a file before removing
        if os.path.isfile(file_path):
            os.remove(file_path)
    results=manual_unpacker.unpack_atlas(packed_texture, "UnpackedTextures", min_area=10)

#for name, dimensions in results.items():
        #print(f"{name}: Height={dimensions[0]}, Width={dimensions[1]}, Area={dimensions[2]}")

#remove background img
#results.pop("object_0", None)
STD_MUT = 0.1
STD_CX = 0.8
STD_POP = 20
STD_GEN = 50

mut_rate = 0.05
mut_results = []
#mutation rate changes
while(mut_rate < 1.0):
    genetic_packer = GeneticAtlasPacker(results, seed=42, mut_rate=mut_rate, cx_rate=STD_CX, atlas_height=1024, atlas_width=1024, pop_size=STD_POP)
    #start_time = time.perf_counter()
    best_individual, best_fitness = genetic_packer.run(generations=STD_GEN)
    #genetic_packer.pack_best()
    #end_time = time.perf_counter()
    empty_space = genetic_packer.empty_space()
    mut_results.append(empty_space)
    mut_rate += 0.05

copy = mut_results.copy()
copy.sort()
best_es = copy[0]
best_mut = mut_results.index(best_es)
best_mut = 0.05 + (0.05 * best_mut)
print(best_mut)

cx_rate = 0.05
cx_results = []
while(cx_rate < 1.0):
    genetic_packer = GeneticAtlasPacker(results, seed=42, mut_rate=STD_MUT, cx_rate=cx_rate, atlas_height=1024, atlas_width=1024, pop_size=STD_POP)
    #start_time = time.perf_counter()
    best_individual, best_fitness = genetic_packer.run(generations=STD_GEN)
    #genetic_packer.pack_best()
    #end_time = time.perf_counter()
    empty_space = genetic_packer.empty_space()
    cx_results.append(empty_space)
    cx_rate += 0.05

copy = cx_results.copy()
copy.sort()
best_es = copy[0]
best_cx = cx_results.index(best_es)
best_cx = 0.05 + (0.05 * best_cx)
print(best_cx)

fig, ax = plt.subplots(figsize=(12, 9))
range = np.arange(0.05, 1, 0.05)
ax.plot(range, cx_results, "o-", label="Crossover Rate")
ax.plot(range, mut_results, "s-", label="Mutation Rate")
ax.set(xlabel="Rate", ylabel="Empty Space", title="Changes in Empty Space Across Different CX and Mut Rates")
ax.set_xticks(range)
ax.legend()
fig.tight_layout()
fig.savefig("param_tuning_visuals/cx_mut_elbow.png")
plt.show()

pop = 10
pop_max = 210
pop_results = []
#mutation rate changes
while(pop < pop_max):
    genetic_packer = GeneticAtlasPacker(results, seed=42, mut_rate=STD_MUT, cx_rate=STD_CX, atlas_height=1024, atlas_width=1024, pop_size=pop)
    #start_time = time.perf_counter()
    best_individual, best_fitness = genetic_packer.run(generations=STD_GEN)
    #genetic_packer.pack_best()
    #end_time = time.perf_counter()
    empty_space = genetic_packer.empty_space()
    pop_results.append(empty_space)
    pop += 10

copy = pop_results.copy()
copy.sort()
best_es = copy[0]
best_pop = pop_results.index(best_es)
best_pop = 10 + (10 * best_pop)
print(best_pop)

fig, ax = plt.subplots(figsize=(10, 8))
range = np.arange(10, 210, 10)
ax.plot(range, pop_results, "o-")
ax.set(xlabel="Population Size", ylabel="Empty Space", title="Changes in Empty Space Across Different Population Sizes")
ax.set_xticks(range)
fig.tight_layout()
fig.savefig("param_tuning_visuals/pop_elbow.png")
plt.show()

gen = 50
max_gen = 1550
gen_results = []
while(gen < max_gen):
    genetic_packer = GeneticAtlasPacker(results, seed=42, mut_rate=best_mut, cx_rate=best_cx, atlas_height=1024, atlas_width=1024, pop_size=best_pop)
    #start_time = time.perf_counter()
    best_individual, best_fitness = genetic_packer.run(generations=gen)
    #genetic_packer.pack_best()
    #end_time = time.perf_counter()
    empty_space = genetic_packer.empty_space()
    gen_results.append(empty_space)
    gen += 50

copy = gen_results.copy()
copy.sort()
best_es = copy[0]
best_gen = gen_results.index(best_es)

fig, ax = plt.subplots(figsize=(10, 8))
range = np.arange(50, 1500, 50)
ax.plot(range, gen_results, "o-")
ax.set(xlabel="Number of Generations", ylabel="Empty Space", title="Changes in Empty Space Across Number of Generations Run")
ax.set_xticks(range)
fig.tight_layout()
fig.savefig("param_tuning_visuals/gen_elbow.png")
plt.show()
#genetic_packer.visualize_atlas(folder_path="UnpackedTextures")
#genetic_packer.export_atlas(folder_path="UnpackedTextures", output_path="PackedTexture/GA_packed.png")
#genetic_packer.export_atlas(output_path="PackedTexture/GA_packed.png")