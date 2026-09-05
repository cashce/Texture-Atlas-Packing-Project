import os
from texture_atlas_packer import TextureAtlasPacker

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
atlas_file = atlas_packer.pack(algorithm="basic_greedy")
#print(f"Packing coordinates: {atlas_file}")

# 4. Visualize the packed atlas
atlas_packer.visualize_atlas(atlas_file)
