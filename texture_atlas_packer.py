import cv2
import numpy as np
import os
import random

#TODO: add diffent heuristic options for algorithm 

# Purpose: Serves as an atlas packer for rectangular textures.
class TextureAtlasPacker:
    # intializes the TextureAtlasPacker object with a list of texture file names, and the folder path where the textures are stored.
    def __init__(self, textures, folder_path=None):
        #self.generated = False
        self.textures = textures
        self.folder_path = folder_path
        self.texture_dimensions = dict() # 'key' = texture file name, 'value' = (height, width, area)
        self.atlas_width = 1024
        self.atlas_height = 1024
        self.algorithm = 'basic_greedy'
        self.packing_coordinates = dict() # 'key' = texture file name, 'value' = (x, y, height, width, rotated)
        self._get_texture_dimensions() # get dimensions of textures and sort based on area

    # manually adjust the dimensions of the atlas file
    def set_atlas_dimensions(self, width, height):
        self.atlas_width = width
        self.atlas_height = height

    # creates a dictionary where key is the texture file name and the value is an array containing the height, width, and area values
    def _get_texture_dimensions(self):
        # get the dimensions of each texture and store them in a dictionary
        for texture in self.textures:
            if (self.folder_path == None):
                # drop rgb value from textures
                self.texture_dimensions = {key: value[:-1] for key, value in self.textures.items()}
                break;        
            texture_file = cv2.imread(os.path.join(self.folder_path, texture))
            height, width = texture_file.shape[:2]
            area = height * width
            self.texture_dimensions[texture] = (height, width, area)

    # sorts textures based on area, perimeter, shortest side, or longest side
    def sort_texture_dimensions(self, type):
        if (type == "area"):
            self.texture_dimensions = dict(sorted(self.texture_dimensions.items(), key=lambda item: item[1][2], reverse=True))
        elif (type == "perimeter"):
            self.texture_dimensions = dict(sorted(self.texture_dimensions.items(), key=lambda item: 2 * (item[1][0] + item[1][1]), reverse=True))
        elif (type == "shortest side"):
            self.texture_dimensions = dict(sorted(self.texture_dimensions.items(), key=lambda item: min(item[1][0], item[1][1])))
        elif (type == "longest side"):
            self.texture_dimensions = dict(sorted(self.texture_dimensions.items(), key=lambda item: max(item[1][0], item[1][1])))
        else:
            print("Invalid sorting type. Permitted Types: area, perimeter, shortest side, longest side")


    # packs the uploaded textures based on algorithm specified by the user and returns the packing coordinates of the textures in the atlas
    def pack(self, algorithm):
        # overwrites previous packed coordinated if pack is called again
        if(len(self.packing_coordinates) != 0):
            new_packing_coordinates = dict()
            self.packing_coordinates = new_packing_coordinates
        # call packing algorithm based on parameter given
        if algorithm == "greedy":
            self._basic_greedy_packer()
        elif algorithm == "skyline":
            self._basic_skyline_packer()
        elif algorithm == "maxrects"    :
            self._basic_maxrects_packer()
        elif algorithm == "guillotine":
            self._basic_guillotine_packer()
        else:
            print("Algorithm not recognized. Accepted algorithms: greedy, skyline, maxrects, guillotine.")
            return None

        # print whitespace calculation
        print(f"Empty space in atlas after packing with {algorithm} algorithm: {self._empty_space_calculation() * 100:.2f}%")

    # opens a gui of the atlas after the texures have been packed by the pack() method
    def visualize_atlas(self):
        # create a blank image of the atlas dimensions
        atlas_image = np.zeros((self.atlas_height, self.atlas_width, 3), dtype=np.uint8)
        # fill the atlas image with the packed textures
        for texture, coordinates in self.packing_coordinates.items():
            x, y, height, width = coordinates[:4]
            rotated = coordinates[4] if len(coordinates) > 4 else False
            if (self.folder_path is not None): 
                # real texture files on disk
                texture_file = cv2.imread(os.path.join(self.folder_path, texture))
            else:
                source = self.textures[texture]
                if isinstance(source, np.ndarray):
                    # an actual image array was supplied directly
                    texture_file = source
                else:
                    # generated shape data (e.g. from ShapeGenerator): (height, width, area, rgb).
                    # no real pixel data exists, so render a solid rectangle in its color instead.
                    # use the original (pre-rotation) dimensions to build the block, then rotate
                    orig_h, orig_w = source[0], source[1]
                    rgb = source[3] if len(source) > 3 else self._random_rgb()
                    texture_file = self._solid_color_rect(orig_h, orig_w, rgb)
            # if the texture was placed rotated 90°, rotate the image block to match the atlas slot
            if rotated:
                texture_file = cv2.rotate(texture_file, cv2.ROTATE_90_CLOCKWISE)
            atlas_image[y:y+height, x:x+width] = texture_file
        # display the atlas image in a window
        cv2.imshow("Texture Atlas", atlas_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # generates a random (r, g, b) color, used when a texture has no color of its own
    def _random_rgb(self):
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # builds a solid-color height x width image block (with a thin darker border so
    # adjacent same-ish colored rectangles remain visually distinguishable in the atlas)
    def _solid_color_rect(self, height, width, rgb):
        r, g, b = rgb
        # cv2/numpy images are stored as BGR, not RGB
        block = np.full((height, width, 3), (b, g, r), dtype=np.uint8)
        border_color = (max(b - 60, 0), max(g - 60, 0), max(r - 60, 0))
        cv2.rectangle(block, (0, 0), (width - 1, height - 1), border_color, thickness=1)
        return block

    # greedy packing algorithm for rectangular textures using first fit decreasing rules (FFD) 
    # rotations disallowed
    def _basic_greedy_packer(self):
        #place largest texture in the top left corner of the atlas and then place the next largest texture in the next available space
        for texture, dimensions in self.texture_dimensions.items():
            height, width, area = dimensions
            # check if the texture can fit in the atlas
            if height > self.atlas_height or width > self.atlas_width:
                #print(f"Texture {texture} is too large to fit in the atlas. Change the atlas dimensions or remove the texture from the list.")
                continue
            # check packing_coordinates to see if the texture can fit in the atlas
            if self.packing_coordinates == {}:
                self.packing_coordinates[texture] = (0, 0, height, width, False)
            else:
                # find the next available space in the atlas
                for y in range(self.atlas_height):
                    for x in range(self.atlas_width):
                        # check if the texture can fit in the atlas at this position
                        if self._can_fit(x, y, height, width):
                            self.packing_coordinates[texture] = (x, y, height, width, False)
                            break
                    else:
                        continue
                    break

    # checks if the texture can fit in the atlas at the given position
    def _can_fit(self, x, y, height, width):
        # check if the texture can fit in the atlas at the given position
        for texture, coordinates in self.packing_coordinates.items():
            x1, y1, h1, w1 = coordinates[:4]
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
            x, y, h, w = vals[:4]
            texture_areas += h * w

        # get total area of atlas file
        atlas_area = self.atlas_width * self.atlas_height
        return (atlas_area - texture_areas) / atlas_area

    # rectangle support, 90-degree rotations allowed
    # skyline bottom-left algorithm: places each texture at the lowest-then-leftmost
    # position along the current skyline profile, minimizing wasted space beneath it.
    # Both the original orientation and 90-degree rotation are tried; the orientation
    # that yields the best (lowest span_y, then least wasted space) placement is used.
    def _basic_skyline_packer(self):
        # skyline segments: list of [x, width, y] covering the full atlas width with no gaps,
        # sorted left to right, where y is the current height of the skyline at that segment
        segments = [[0, self.atlas_width, 0]]

        # loop through each texture (largest area first) to place it in the atlas
        for texture, dimensions in self.texture_dimensions.items():
            height, width, area = dimensions

            # check if the texture can ever fit in the atlas in either orientation
            fits_normal  = width <= self.atlas_width and height <= self.atlas_height
            fits_rotated = height <= self.atlas_width and width <= self.atlas_height
            if not fits_normal and not fits_rotated:
                #print(f"Texture {texture} is too large to fit in the atlas. Change the atlas dimensions or remove the texture from the list.")
                continue

            # orientations to try: (place_w, place_h, rotated_flag)
            orientations = []
            if fits_normal:
                orientations.append((width, height, False))
            if fits_rotated and (height, width) != (width, height):
                orientations.append((height, width, True))

            best = None  # (span_y, wasted_space, x, place_w, place_h, rotated)

            for place_w, place_h, rotated in orientations:
                # try placing the texture starting at each segment's left edge
                for i in range(len(segments)):
                    x = segments[i][0]
                    if x + place_w > self.atlas_width:
                        continue

                    # find the highest skyline point spanned by the texture's width
                    span_y = 0
                    j = i
                    while j < len(segments) and segments[j][0] < x + place_w:
                        span_y = max(span_y, segments[j][2])
                        j += 1

                    if span_y + place_h > self.atlas_height:
                        continue

                    # wasted space = area between the placed texture's bottom and the skyline beneath it
                    wasted_space = 0
                    j = i
                    while j < len(segments) and segments[j][0] < x + place_w:
                        seg_x, seg_w, seg_y = segments[j]
                        overlap = min(seg_x + seg_w, x + place_w) - max(seg_x, x)
                        wasted_space += (span_y - seg_y) * overlap
                        j += 1

                    candidate = (span_y, wasted_space, x, place_w, place_h, rotated)
                    if best is None or candidate[:2] < best[:2]:
                        best = candidate

            # if no candidate position was found, the texture cannot be placed
            if best is None:
                #print(f"Texture {texture} could not be placed in the atlas. Change the atlas dimensions or remove the texture from the list.")
                continue

            best_y, best_wasted_space, best_x, place_w, place_h, rotated = best

            # record the placement — store (h, w) as they appear in the atlas slot
            placed_h = place_h  # height in atlas = place_h
            placed_w = place_w  # width  in atlas = place_w
            self.packing_coordinates[texture] = (best_x, best_y, placed_h, placed_w, rotated)

            # update the skyline to reflect the newly placed texture
            self._update_skyline(segments, best_x, place_w, best_y + place_h)

    # internal method used by _basic_skyline_packer to update the skyline profile
    # after placing a texture: splits/removes segments under the texture, inserts a
    # new segment at the texture's top edge, and merges adjacent segments of equal height
    def _update_skyline(self, segments, x, width, new_y):
        x_end = x + width
        remaining = []
        for seg_x, seg_w, seg_y in segments:
            seg_end = seg_x + seg_w
            if seg_end <= x or seg_x >= x_end:
                # segment does not overlap the placed texture at all
                remaining.append([seg_x, seg_w, seg_y])
                continue
            # keep the portion of the segment to the left of the placed texture
            if seg_x < x:
                remaining.append([seg_x, x - seg_x, seg_y])
            # keep the portion of the segment to the right of the placed texture
            if seg_end > x_end:
                remaining.append([x_end, seg_end - x_end, seg_y])

        # insert the new segment representing the top of the placed texture
        remaining.append([x, width, new_y])
        remaining.sort(key=lambda seg: seg[0])

        # merge adjacent segments that share the same height
        merged = []
        for seg in remaining:
            if merged and merged[-1][2] == seg[2] and merged[-1][0] + merged[-1][1] == seg[0]:
                merged[-1][1] += seg[1]
            else:
                merged.append(seg)

        segments[:] = merged

    # rectangle support, 90-degree rotations allowed
    # MAXRECTS-BAF (best area fit): tracks the set of maximal free rectangles remaining
    # in the atlas, places each texture in the free rectangle that leaves the least
    # leftover area, trying both normal and 90-degree rotated orientations.
    def _basic_maxrects_packer(self):
        # free rectangles stored as [x, y, width, height]
        free_rects = [[0, 0, self.atlas_width, self.atlas_height]]

        for texture, dimensions in self.texture_dimensions.items():
            height, width, area = dimensions

            fits_normal  = width <= self.atlas_width and height <= self.atlas_height
            fits_rotated = height <= self.atlas_width and width <= self.atlas_height
            if not fits_normal and not fits_rotated:
                #print(f"Texture {texture} is too large to fit in the atlas. Change the atlas dimensions or remove the texture from the list.")
                continue

            # orientations to try: (place_w, place_h, rotated_flag)
            orientations = []
            if fits_normal:
                orientations.append((width, height, False))
            if fits_rotated and (height, width) != (width, height):
                orientations.append((height, width, True))

            # find the free rectangle + orientation that fits with the least leftover area
            best_idx = -1
            best_leftover = None
            best_place_w = width
            best_place_h = height
            best_rotated = False

            for place_w, place_h, rotated in orientations:
                for i, (x, y, w, h) in enumerate(free_rects):
                    if place_w <= w and place_h <= h:
                        leftover = (w * h) - (place_w * place_h)
                        if best_leftover is None or leftover < best_leftover:
                            best_leftover = leftover
                            best_idx = i
                            best_place_w = place_w
                            best_place_h = place_h
                            best_rotated = rotated

            if best_idx == -1:
                #print(f"Texture {texture} could not be placed in the atlas. Change the atlas dimensions or remove the texture from the list.")
                continue

            place_x, place_y = free_rects[best_idx][0], free_rects[best_idx][1]
            placed_rect = [place_x, place_y, best_place_w, best_place_h]

            # record the placement
            self.packing_coordinates[texture] = (place_x, place_y, best_place_h, best_place_w, best_rotated)

            # split every free rectangle that overlaps the placed texture into the
            # (up to four) maximal free rectangles that remain around it
            new_free_rects = []
            for free_rect in free_rects:
                if self._rects_intersect(free_rect, placed_rect):
                    new_free_rects.extend(self._split_free_rect(free_rect, placed_rect))
                else:
                    new_free_rects.append(free_rect)
            free_rects = new_free_rects

            # prune any free rectangle that is fully contained within another,
            # since it no longer represents usable space of its own
            free_rects = self._merge(free_rects)

    # internal method used by _basic_maxrects_packer to test whether two
    # [x, y, width, height] rectangles overlap
    def _rects_intersect(self, a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return not (bx >= ax + aw or bx + bw <= ax or by >= ay + ah or by + bh <= ay)

    # internal method used by _basic_maxrects_packer to split a free rectangle
    # around a rectangle that was just placed inside (or overlapping) it, returning
    # the (up to four) maximal free rectangles that remain: left, right, above, below
    def _split_free_rect(self, free_rect, used_rect):
        fx, fy, fw, fh = free_rect
        ux, uy, uw, uh = used_rect
        results = []

        if ux > fx:
            results.append([fx, fy, ux - fx, fh])
        if ux + uw < fx + fw:
            results.append([ux + uw, fy, (fx + fw) - (ux + uw), fh])
        if uy > fy:
            results.append([fx, fy, fw, uy - fy])
        if uy + uh < fy + fh:
            results.append([fx, uy + uh, fw, (fy + fh) - (uy + uh)])

        return results

    # rectangle support, 90-degree rotations allowed
    # guillotine packer: places each texture in the free region with the least leftover
    # area, trying both normal and 90-degree rotated orientations, then splits that
    # region into two new regions with a single straight (guillotine) cut, choosing
    # the cut axis that minimizes the worse leftover sliver
    def _basic_guillotine_packer(self):
        # free regions stored as [x, y, width, height]
        free_regions = [[0, 0, self.atlas_width, self.atlas_height]]

        for texture, dimensions in self.texture_dimensions.items():
            height, width, area = dimensions

            fits_normal  = width <= self.atlas_width and height <= self.atlas_height
            fits_rotated = height <= self.atlas_width and width <= self.atlas_height
            if not fits_normal and not fits_rotated:
                #print(f"Texture {texture} is too large to fit in the atlas. Change the atlas dimensions or remove the texture from the list.")
                continue

            # orientations to try: (place_w, place_h, rotated_flag)
            orientations = []
            if fits_normal:
                orientations.append((width, height, False))
            if fits_rotated and (height, width) != (width, height):
                orientations.append((height, width, True))

            # find the free region + orientation with the least leftover area
            best_idx = -1
            best_leftover = None
            best_place_w = width
            best_place_h = height
            best_rotated = False

            for place_w, place_h, rotated in orientations:
                for i, (x, y, w, h) in enumerate(free_regions):
                    if place_w <= w and place_h <= h:
                        leftover = (w * h) - (place_w * place_h)
                        if best_leftover is None or leftover < best_leftover:
                            best_leftover = leftover
                            best_idx = i
                            best_place_w = place_w
                            best_place_h = place_h
                            best_rotated = rotated

            if best_idx == -1:
                #print(f"Texture {texture} could not be placed in the atlas. Change the atlas dimensions or remove the texture from the list.")
                continue

            x, y, w, h = free_regions.pop(best_idx)

            # place the texture in the top-left corner of the chosen region
            self.packing_coordinates[texture] = (x, y, best_place_h, best_place_w, best_rotated)

            leftover_w = w - best_place_w
            leftover_h = h - best_place_h

            # split the remaining L-shaped space with a single guillotine cut, choosing
            # the axis that leaves the smaller (less wasteful) sliver of leftover space
            new_regions = []
            if leftover_w > 0 and leftover_h > 0:
                if leftover_w <= leftover_h:
                    # vertical cut: right region spans the full region height,
                    # bottom region spans only the placed texture's width
                    new_regions.append([x + best_place_w, y, leftover_w, h])
                    new_regions.append([x, y + best_place_h, best_place_w, leftover_h])
                else:
                    # horizontal cut: bottom region spans the full region width,
                    # right region spans only the placed texture's height
                    new_regions.append([x, y + best_place_h, w, leftover_h])
                    new_regions.append([x + best_place_w, y, leftover_w, best_place_h])
            elif leftover_w > 0:
                new_regions.append([x + best_place_w, y, leftover_w, h])
            elif leftover_h > 0:
                new_regions.append([x, y + best_place_h, w, leftover_h])

            free_regions.extend(new_regions)

            # prune any free region that is fully contained within another,
            # since it no longer represents usable space of its own
            free_regions = self._merge(free_regions)

    # internal method used by _basic_guillotine_packer and _basic_maxrects_packer to
    # prune free rectangles that are fully contained within another free rectangle
    # (and therefore redundant), keeping the free list small and non-overlapping-heavy
    def _merge(self, free_regions):
        # remove exact duplicates while preserving order
        unique = list(dict.fromkeys(tuple(r) for r in free_regions))

        pruned = []
        for i, rect in enumerate(unique):
            ix, iy, iw, ih = rect
            contained = False
            for j, other in enumerate(unique):
                if i == j:
                    continue
                ox, oy, ow, oh = other
                if ix >= ox and iy >= oy and ix + iw <= ox + ow and iy + ih <= oy + oh:
                    contained = True
                    break
            if not contained:
                pruned.append(list(rect))

        return pruned


