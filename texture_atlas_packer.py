import cv2
import numpy as np
import os

# Purpose: Serves as an atlas packer for rectangular textures.
class TextureAtlasPacker:
    # intializes the TextureAtlasPacker object with a list of texture file names, and the folder path where the textures are stored.
    def __init__(self, textures, folder_path):
        self.textures = textures
        self.folder_path = folder_path
        self.texture_dimensions = dict() # 'key' = texture file name, 'value' = (height, width, area)
        self.atlas_width = 1024
        self.atlas_height = 1024
        self.algorithm = 'basic_greedy'
        self.packing_coordinates = dict() # 'key' = texture file name, 'value' = (x, y, height, width)
        #self.get_texture_dimensions(self)

    # manually adjust the dimensions of the atlas file
    def set_atlas_dimensions(self, width, height):
        self.atlas_width = width
        self.atlas_height = height

    # creates a dictionary where key is the texture file name and the value is an array containing the height, width, and area values
    def get_texture_dimensions(self):
        # get the dimensions of each texture and store them in a dictionary
        for texture in self.textures:
            texture_file = cv2.imread(os.path.join(self.folder_path, texture))
            height, width = texture_file.shape[:2]
            area = height * width
            self.texture_dimensions[texture] = (height, width, area)
        # sort the dictionary based on area in descending order
        self.texture_dimensions = dict(sorted(self.texture_dimensions.items(), key=lambda item: item[1][2], reverse=True))
        

    # packs the uploaded textures based on algorithm specified by the user and returns the packing coordinates of the textures in the atlas
    def pack(self, algorithm):
        # get dimensions of textures and sort based on area
        self.get_texture_dimensions()

        # call packing algorithm based on parameter given
        if algorithm == "basic_greedy":
            self._basic_greedy_packer()
        else:
            print("Algorithm not recognized. Please use 'basic_greedy'.")
            return None

        # print whitespace calculation
        print(f"Empty space in atlas after packing: {self._empty_space_calculation() * 100:.2f}%")

        # return the packing coordinates of the textures in the atlas
        return self.packing_coordinates

    # opens a gui of the atlas after the texures have been packed by the pack() method
    def visualize_atlas(self, atlas_file):
        # create a blank image of the atlas dimensions
        atlas_image = np.zeros((self.atlas_height, self.atlas_width, 3), dtype=np.uint8)
        # fill the atlas image with the packed textures
        for texture, coordinates in self.packing_coordinates.items():
            x, y, height, width = coordinates
            texture_file = cv2.imread(os.path.join(self.folder_path, texture))
            atlas_image[y:y+height, x:x+width] = texture_file
        # display the atlas image in a window
        cv2.imshow("Texture Atlas", atlas_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # greedy packing algorithm for rectangular textures using first fit decreasing rules (FFD) 
    # rotations disallowed
    def _basic_greedy_packer(self):
        #place largest texture in the top left corner of the atlas and then place the next largest texture in the next available space
        for texture, dimensions in self.texture_dimensions.items():
            height, width, area = dimensions
            # check if the texture can fit in the atlas
            if height > self.atlas_height or width > self.atlas_width:
                print(f"Texture {texture} is too large to fit in the atlas. Change the atlas dimensions or remove the texture from the list.")
                continue
            # check packing_coordinates to see if the texture can fit in the atlas
            if self.packing_coordinates == {}:
                self.packing_coordinates[texture] = (0, 0, height, width)
            else:
                # find the next available space in the atlas
                for y in range(self.atlas_height):
                    for x in range(self.atlas_width):
                        # check if the texture can fit in the atlas at this position
                        if self._can_fit(x, y, height, width):
                            self.packing_coordinates[texture] = (x, y, height, width)
                            break
                    else:
                        continue
                    break

    # checks if the texture can fit in the atlas at the given position
    def _can_fit(self, x, y, height, width):
        # check if the texture can fit in the atlas at the given position
        for texture, coordinates in self.packing_coordinates.items():
            x1, y1, h1, w1 = coordinates
            if (x < x1 + w1 and x + width > x1 and y < y1 + h1 and y + height > y1):
                return False
            elif(x + width > self.atlas_width or y + height > self.atlas_height):
                return False
        return True

    # calculates the proportion of space left empty in the atlas after packing
    def _empty_space_calculation(self):
        # sum areas of packed textures
        texture_areas = 0
        for texture, vals in self.packing_coordinates.items():
            x, y, h, w = vals
            texture_areas += h * w

        # get total area of atlas file
        atlas_area = self.atlas_width * self.atlas_height
        return (atlas_area - texture_areas) / atlas_area



