import os

import cv2
import numpy as np


def unpack_atlas(input_png, output_dir, prefix="object", min_area=1):
    """
    Extract every distinct, non-transparent object from a PNG sprite-sheet /
    texture atlas and save each one as its own PNG file.

    The function uses the image's alpha channel to locate objects: any
    connected group of non-transparent pixels is treated as a single object.
    Each extracted object is saved as a tight bounding-box crop that preserves
    the original RGBA data (transparency included).

    Parameters
    ----------
    input_png : str
        Path to the source PNG file.  The image must have an alpha channel
        (RGBA).  If the file has no alpha channel a synthetic one is created
        from the non-black pixels.
    output_dir : str
        Directory where the extracted PNG files will be written.  Created
        automatically if it does not already exist.
    prefix : str, optional
        Filename prefix for each extracted object (default ``"object"``).
        Files are named ``<prefix>_0.png``, ``<prefix>_1.png``, ...
    min_area : int, optional
        Minimum bounding-box area (width x height, in pixels) a connected
        component must have to be kept.  Tiny noise components smaller than
        this threshold are ignored (default ``1``).

    Returns
    -------
    dict
        A dictionary where:
        - **key** - the output filename (basename only, e.g. ``"object_0.png"``)
        - **value** - ``[height, width, area]`` of the extracted crop
          (area = height x width of the tight bounding box)

    Raises
    ------
    FileNotFoundError
        If *input_png* does not exist or cannot be read by OpenCV.
    ValueError
        If the loaded image has an unexpected number of channels.

    Example
    -------
    >>> result = unpack_atlas("PackedTexture/BlenderPackedTrans.png",
    ...                       "UnpackedTextures")
    >>> for name, dims in result.items():
    ...     print(name, dims)
    object_0.png [120, 80, 9600]
    object_1.png [64, 200, 12800]
    """
    # -- 1. Load image ---------------------------------------------------------
    img = cv2.imread(input_png, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {input_png}")

    if img.ndim == 2:
        # Grayscale -- add a full-opacity alpha channel
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        # BGR without alpha -- synthesise alpha from non-black pixels
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        alpha = np.where(gray > 0, 255, 0).astype(np.uint8)
        img = cv2.merge([img[:, :, 0], img[:, :, 1], img[:, :, 2], alpha])
    elif img.shape[2] != 4:
        raise ValueError(
            f"Unexpected number of channels ({img.shape[2]}) in {input_png}. "
            "Expected 1, 3, or 4."
        )

    # -- 2. Build binary mask from alpha channel --------------------------------
    alpha_channel = img[:, :, 3]
    # Any pixel with alpha > 0 is considered part of an object
    _, mask = cv2.threshold(alpha_channel, 0, 255, cv2.THRESH_BINARY)

    # -- 3. Find connected components ------------------------------------------
    # Use connected-component labelling (8-connectivity) to separate objects
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )
    # stats columns: CC_STAT_LEFT, CC_STAT_TOP, CC_STAT_WIDTH, CC_STAT_HEIGHT, CC_STAT_AREA
    # Label 0 is the background -- skip it

    # -- 4. Prepare output directory -------------------------------------------
    os.makedirs(output_dir, exist_ok=True)

    # -- 5. Crop and save each object ------------------------------------------
    result = {}
    saved_idx = 0

    for label in range(1, num_labels):
        x    = stats[label, cv2.CC_STAT_LEFT]
        y    = stats[label, cv2.CC_STAT_TOP]
        w    = stats[label, cv2.CC_STAT_WIDTH]
        h    = stats[label, cv2.CC_STAT_HEIGHT]
        area = h * w  # bounding-box area

        if area < min_area:
            continue  # skip noise / tiny fragments

        # Crop the bounding-box region from the original RGBA image
        crop = img[y:y + h, x:x + w].copy()

        # Zero out pixels that belong to other objects within this bounding box
        # (only keep the pixels whose label matches the current component)
        component_mask = (labels[y:y + h, x:x + w] == label).astype(np.uint8) * 255
        crop[:, :, 3] = cv2.bitwise_and(crop[:, :, 3], component_mask)

        # Save the crop as a PNG (lossless, alpha preserved)
        filename = f"{prefix}_{saved_idx}.png"
        out_path = os.path.join(output_dir, filename)
        cv2.imwrite(out_path, crop)

        result[filename] = [h, w, area]
        saved_idx += 1

    print(f"Extracted {saved_idx} object(s) from '{input_png}' -> '{output_dir}'")
    return result

