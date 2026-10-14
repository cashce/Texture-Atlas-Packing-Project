import copy
import os
import random

import cv2
import numpy as np

from deap import base, creator, tools

from texture_atlas_packer import TextureAtlasPacker


# ---------------------------------------------------------------------------
# Fitness type – we minimise a single objective (lower bounding area = better)
# ---------------------------------------------------------------------------
if not hasattr(creator, "FitnessMin"):
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMin)


class GeneticAtlasPacker:
    """
    Genetic algorithm for rectangle packing.

    Each *individual* in the population is a list of (texture_key, rotated)
    tuples that defines:
      - the order in which rectangles are fed to the skyline packer, and
      - whether each rectangle is pre-rotated 90 degrees before packing.

    Parameters
    ----------
    textures : dict
        Same format accepted by TextureAtlasPacker:
        { name: (height, width, area, rgb?) }
    pop_size : int
        Number of individuals in the population.
    cx_rate : float
        Probability [0, 1] of applying crossover to the two parents when
        producing an offspring.
    mut_rate : float
        Per-gene probability [0, 1] of flipping a rectangle's rotation flag
        during mutation.
    algorithm : str
        Underlying packing heuristic.  Currently only ``"skyline"`` is
        supported inside this GA (the heuristic used by _pack_individual).
        The string is stored for reference / future extension.
    seed : int
        Random seed used to shuffle the initial population.
    fitness_fn : callable or None
        Optional override for the fitness function.  Must accept a single
        individual (list of (key, rotated) tuples) and return a 1-tuple
        ``(score,)`` where *lower is better*.  When ``None`` the built-in
        skyline-bounding-area fitness is used.
    atlas_width : int
        Width of the target atlas canvas (pixels).
    atlas_height : int
        Height of the target atlas canvas (pixels).
    """

    def __init__(
        self,
        textures,
        pop_size=20,
        cx_rate=0.8,
        mut_rate=0.1,
        algorithm="skyline",
        seed=42,
        fitness_fn=None,
        atlas_width=1024,
        atlas_height=1024,
    ):
        self.textures = textures
        self.pop_size = pop_size
        self.cx_rate = cx_rate
        self.mut_rate = mut_rate
        self.algorithm = algorithm
        self.seed = seed
        self.atlas_width = atlas_width
        self.atlas_height = atlas_height

        # Use the provided fitness function or fall back to the built-in one
        self._fitness_fn = fitness_fn if fitness_fn is not None else self._skyline_fitness

        # Ordered list of texture keys – the "gene alphabet"
        self._keys = list(textures.keys())

        # DEAP toolbox wired to this instance's operators
        self._toolbox = self._build_toolbox()

        # Population and best individual are populated by run()
        self.population = []
        self.best_individual = None
        self.best_fitness = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, generations=50):
        """
        Execute the genetic algorithm for *generations* iterations.

        Returns
        -------
        best : list of (key, rotated) tuples
            The individual with the lowest fitness score found.
        best_fitness : float
            The fitness value of the best individual.
        """
        random.seed(self.seed)

        # ── 1. Initialise population ──────────────────────────────────────
        self.population = [self._toolbox.individual() for _ in range(self.pop_size)]

        # ── 2. Evaluate initial population ───────────────────────────────
        for ind in self.population:
            ind.fitness.values = self._toolbox.evaluate(ind)

        # ── 3. Evolve ─────────────────────────────────────────────────────
        for gen in range(generations):
            # Select the two best parents (elites)
            sorted_pop = sorted(self.population, key=lambda ind: ind.fitness.values[0])
            parent1 = sorted_pop[0]
            parent2 = sorted_pop[1]

            # Produce one offspring via crossover (maybe) then mutation
            offspring = self._toolbox.clone(parent1)
            if random.random() < self.cx_rate:
                offspring, _ = self._toolbox.mate(offspring, self._toolbox.clone(parent2))
                del offspring.fitness.values  # fitness is now stale

            offspring = self._toolbox.mutate(offspring)[0]
            del offspring.fitness.values  # ensure re-evaluation after mutation

            # Evaluate the offspring
            offspring.fitness.values = self._toolbox.evaluate(offspring)

            # Replace the weakest member of the population with the offspring
            weakest_idx = max(
                range(len(self.population)),
                key=lambda i: self.population[i].fitness.values[0],
            )
            self.population[weakest_idx] = offspring

        # ── 4. Return the best individual found ───────────────────────────
        self.best_individual = min(self.population, key=lambda ind: ind.fitness.values[0])
        self.best_fitness = self.best_individual.fitness.values[0]
        return self.best_individual, self.best_fitness

    def pack_best(self):
        """
        Run the skyline packer with the best individual found after ``run()``.

        Returns
        -------
        TextureAtlasPacker
            A packer whose ``packing_coordinates`` reflects the best ordering.
        """
        if self.best_individual is None:
            raise RuntimeError("Call run() before pack_best().")
        return self._pack_individual(self.best_individual)

    # ------------------------------------------------------------------
    # DEAP toolbox construction
    # ------------------------------------------------------------------

    def _build_toolbox(self):
        toolbox = base.Toolbox()

        # Individual factory
        toolbox.register("individual", self._make_individual)

        # Genetic operators
        toolbox.register("mate",    self._cx_order)
        toolbox.register("mutate",  self._mut_rotate, mut_rate=self.mut_rate)
        toolbox.register("evaluate", self._fitness_fn)
        toolbox.register("clone",   copy.deepcopy)

        return toolbox

    # ------------------------------------------------------------------
    # Individual creation
    # ------------------------------------------------------------------

    def _make_individual(self):
        """
        Create one individual: a shuffled list of (texture_key, rotated) pairs.
        Each rectangle starts with rotated=False; the shuffle gives a random
        packing order.
        """
        genes = [(key, False) for key in self._keys]
        random.shuffle(genes)
        return creator.Individual(genes)

    # ------------------------------------------------------------------
    # Crossover – Order Crossover (OX1) extended to carry rotation bits
    # ------------------------------------------------------------------

    def _cx_order(self, ind1, ind2):
        """
        Order Crossover (OX1) on the texture-key sequence.

        A contiguous slice is copied verbatim from *ind1* into the child.
        The remaining positions are filled with keys from *ind2* in their
        relative order, skipping keys already present.  The *rotated* flag
        for each gene comes from whichever parent contributed that key.

        Both *ind1* and *ind2* are modified in-place (DEAP convention) and
        returned.  In practice the caller only uses the first return value.
        """
        size = len(ind1)
        if size < 2:
            return ind1, ind2

        # Choose a random contiguous slice from ind1
        cx_start = random.randint(0, size - 1)
        cx_end   = random.randint(cx_start + 1, size)  # exclusive

        # Build a rotation-flag lookup from each parent keyed by texture name
        rot1 = {key: rot for key, rot in ind1}
        rot2 = {key: rot for key, rot in ind2}

        # Keys contributed by ind1 in the slice (preserve order)
        slice_keys = [ind1[i][0] for i in range(cx_start, cx_end)]
        slice_set  = set(slice_keys)

        # Keys from ind2 that are NOT already in the slice, in ind2 order
        remainder = [key for key, _ in ind2 if key not in slice_set]

        # Fill the child: positions outside the slice come from ind2's order
        child_genes = [None] * size
        for i in range(cx_start, cx_end):
            key = ind1[i][0]
            child_genes[i] = (key, rot1[key])

        rem_iter = iter(remainder)
        for i in range(size):
            if child_genes[i] is None:
                key = next(rem_iter)
                child_genes[i] = (key, rot2[key])

        # Overwrite ind1 in-place (DEAP expects in-place modification)
        ind1[:] = child_genes
        return ind1, ind2

    # ------------------------------------------------------------------
    # Mutation – randomly flip rotation flags
    # ------------------------------------------------------------------

    def _mut_rotate(self, individual, mut_rate):
        """
        For each gene independently, flip the *rotated* flag with probability
        *mut_rate*.  Rotating a rectangle 90° may allow it to fit better in a
        narrow skyline gap.
        """
        for i in range(len(individual)):
            if random.random() < mut_rate:
                key, rotated = individual[i]
                individual[i] = (key, not rotated)
        return (individual,)

    # ------------------------------------------------------------------
    # Skyline packing of a single individual
    # ------------------------------------------------------------------

    def _pack_individual(self, individual):
        """
        Pack the rectangles described by *individual* using the skyline
        bottom-left algorithm from TextureAtlasPacker, respecting the
        individual's ordering and per-rectangle rotation flags.

        The rotation flag in the individual pre-swaps height and width before
        the skyline heuristic sees the rectangle.  The skyline heuristic may
        then *additionally* rotate a rectangle if that produces a better fit
        (since TextureAtlasPacker._basic_skyline_packer also tries both
        orientations).  The net rotation recorded in packing_coordinates
        captures the combined effect.

        Returns
        -------
        TextureAtlasPacker
            Packer with ``packing_coordinates`` populated.
        """
        # Build an ordered texture_dimensions dict that honours the individual's
        # gene order.  Pre-apply the individual's rotation by swapping h/w.
        ordered_dims = {}
        for key, rotated in individual:
            if key not in self.textures:
                continue
            src = self.textures[key]
            orig_h, orig_w = src[0], src[1]
            area = src[2]
            if rotated:
                # Pre-rotate: swap h and w before feeding to the packer
                ordered_dims[key] = (orig_w, orig_h, area)
            else:
                ordered_dims[key] = (orig_h, orig_w, area)

        # Create a packer, inject the ordered dimensions, and run skyline
        packer = TextureAtlasPacker.__new__(TextureAtlasPacker)
        packer.textures          = self.textures
        packer.folder_path       = None
        packer.texture_dimensions = ordered_dims
        packer.atlas_width       = self.atlas_width
        packer.atlas_height      = self.atlas_height
        packer.algorithm         = "skyline"
        packer.packing_coordinates = {}

        packer._basic_skyline_packer()
        return packer

    # ------------------------------------------------------------------
    # Built-in fitness function – skyline bounding-area
    # ------------------------------------------------------------------

    def _skyline_fitness(self, individual):
        """
        Fitness = atlas_width × (height of the highest packed rectangle).

        This is the area of the bounding rectangle that encloses all packed
        textures, ignoring holes within the skyline.  Minimising this score
        drives rectangles to pack as low (and as flat) as possible.

        An individual that fails to place *all* rectangles is penalised by
        the full atlas area multiplied by the fraction of unplaced rectangles.

        Returns a 1-tuple (score,) as required by DEAP.
        """
        packer = self._pack_individual(individual)
        coords = packer.packing_coordinates

        if not coords:
            # Nothing was placed – worst possible score
            return (self.atlas_width * self.atlas_height,)

        # Maximum y-extent across all placed rectangles = skyline ceiling
        max_y = max(y + h for (x, y, h, w, *_) in coords.values())

        bounding_area = self.atlas_width * max_y

        # Penalty for unplaced rectangles: scale bounding area upward
        n_total   = len(self._keys)
        n_placed  = len(coords)
        n_missing = n_total - n_placed
        if n_missing > 0:
            penalty = (n_missing / n_total) * self.atlas_width * self.atlas_height
            bounding_area += penalty

        return (float(bounding_area),)

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------

    def visualize_atlas(self, folder_path=None):
        """
        Display the best packing found by ``run()`` in an OpenCV window.

        Supports two texture sources:
        - **Real image files** – pass *folder_path* to the directory that
          contains the image files.  Each texture key is treated as a
          filename inside that directory.
        - **Generated shapes** – leave *folder_path* as ``None``.  Textures
          must be in ShapeGenerator format ``(height, width, area, rgb)``.
          A solid-colour rectangle is rendered for each shape using its RGB
          value, with a thin darker border so adjacent same-colour blocks
          remain visually distinct.

        If the rotation flag stored in ``packing_coordinates`` is ``True``,
        the image block is rotated 90° clockwise before being blitted onto
        the canvas so it matches the atlas slot exactly.

        Raises
        ------
        RuntimeError
            If called before ``run()`` / ``pack_best()``.
        """
        if self.best_individual is None:
            raise RuntimeError("Call run() before visualize_atlas().")

        packer = self.pack_best()
        coords = packer.packing_coordinates

        # Blank canvas – black background
        atlas_image = np.zeros((self.atlas_height, self.atlas_width, 3), dtype=np.uint8)

        for texture, coordinates in coords.items():
            x, y, height, width = coordinates[:4]
            rotated = coordinates[4] if len(coordinates) > 4 else False

            if folder_path is not None:
                # Real texture file on disk
                texture_file = cv2.imread(os.path.join(folder_path, texture))
            else:
                source = self.textures[texture]
                if isinstance(source, np.ndarray):
                    # A raw image array was supplied directly
                    texture_file = source
                else:
                    # ShapeGenerator format: (height, width, area, rgb).
                    # Build the block to match the atlas slot.
                    # When rotated=True, cv2.rotate will swap h and w, so we
                    # build at (width, height) pre-rotation so it lands as
                    # (height, width) after the rotate call below.
                    block_h = width  if rotated else height
                    block_w = height if rotated else width
                    rgb = source[3] if len(source) > 3 else self._random_rgb()
                    texture_file = self._solid_color_rect(block_h, block_w, rgb)

            # Apply 90° clockwise rotation when the skyline heuristic rotated the slot
            if rotated:
                texture_file = cv2.rotate(texture_file, cv2.ROTATE_90_CLOCKWISE)

            atlas_image[y:y + height, x:x + width] = texture_file

        cv2.imshow("Genetic Atlas", atlas_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # ------------------------------------------------------------------
    # Empty-space calculation
    # ------------------------------------------------------------------

    def empty_space(self):
        """
        Compute the proportion of the atlas canvas left empty after the best
        packing produced by ``run()``.

        Returns
        -------
        float
            A value in ``[0, 1]`` where ``0.0`` means the atlas is completely
            filled and ``1.0`` means nothing was placed.  Printed as a
            percentage for convenience.

        Raises
        ------
        RuntimeError
            If called before ``run()``.
        """
        if self.best_individual is None:
            raise RuntimeError("Call run() before empty_space().")

        packer = self.pack_best()
        coords = packer.packing_coordinates

        packed_area = sum(h * w for (x, y, h, w, *_) in coords.values())
        atlas_area  = self.atlas_width * self.atlas_height
        fraction    = (atlas_area - packed_area) / atlas_area

        print(f"Empty space in atlas after GA packing: {fraction * 100:.2f}%")
        return fraction

    # ------------------------------------------------------------------
    # Internal helpers (mirrors of TextureAtlasPacker helpers)
    # ------------------------------------------------------------------

    def _random_rgb(self):
        """Return a random (r, g, b) colour tuple."""
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def _solid_color_rect(self, height, width, rgb):
        """
        Build a solid-colour ``height × width`` BGR image block with a thin
        darker border so adjacent same-coloured rectangles stay visually
        distinct in the atlas.
        """
        r, g, b = rgb
        # cv2 / numpy images are stored as BGR
        block = np.full((height, width, 3), (b, g, r), dtype=np.uint8)
        border_color = (max(b - 60, 0), max(g - 60, 0), max(r - 60, 0))
        cv2.rectangle(block, (0, 0), (width - 1, height - 1), border_color, thickness=1)
        return block