import os
import time
import manual_unpacker;
from genetic_atlas_packer import GeneticAtlasPacker

def is_dir_empty_fast(dir_path):
    try:
        with os.scandir(dir_path) as entries:
            # any() will return True as soon as it finds the first entry
            return not any(entries)
    except FileNotFoundError:
        return False  # Handle case where directory doesn't exist

folder_path = "PackedTexture"
packed_texture = folder_path + "/Vampire_diffuse_transparent.png"
if is_dir_empty_fast("UnpackedTextures"):
    results=manual_unpacker.unpack_atlas(packed_texture, "UnpackedTextures", min_area=100)
else:
    for filename in os.listdir("UnpackedTextures"):
        # Construct full file path
        file_path = os.path.join("UnpackedTextures", filename)
    
        # Ensure it's a file before removing
        if os.path.isfile(file_path):
            os.remove(file_path)
    results=manual_unpacker.unpack_atlas(packed_texture, "UnpackedTextures", min_area=100)

#for name, dimensions in results.items():
        #print(f"{name}: Height={dimensions[0]}, Width={dimensions[1]}, Area={dimensions[2]}")

#remove background img
results.pop("object_0", None)

genetic_packer = GeneticAtlasPacker(results, seed=42, mut_rate=0.1, cx_rate=0.8, atlas_height=2048, atlas_width=2048, pop_size=20)
#start_time = time.perf_counter()
best_individual, best_fitness = genetic_packer.run(generations=50)
genetic_packer.pack_best()
#end_time = time.perf_counter()
empty_space = genetic_packer.empty_space()

#print(best_individual)

#genetic_packer.visualize_atlas(folder_path="UnpackedTextures")
genetic_packer.export_atlas(folder_path="UnpackedTextures", output_path="PackedTexture/GA_packed.png")

