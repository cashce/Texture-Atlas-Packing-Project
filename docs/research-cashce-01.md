# Traditional and Quantum Genetic Algorithm Comparison
Last Updated: 15 October 2026

## Quantum Computing Background
**Qubit:** smallest unit of information storage in quantum computing. Can be in a state of 1, 0, or superposition of both.
- The probabilities of a qubit being in state 0 and being in state 1 must equal 1.
- A quantum register of $m$ qubits can represent $2^m$ values simultaneously
	- when 'measure' is taken, superposition is destroyed and only one value can be used
## QGA Structure
- Quantum registers act as chromosomes, so chromosomes can represent the superposition of all possible states
**Initialization:** population is created by initializing the amplitude of the qubits by $1/(2^{1/2})$ , so all quantum superposition states are represented by a chromosome with equal probability.
**Fitness Eval:** refer to 3.2.3. this made no sense
**Quantum Genetic Operations:** 
1. **Measuring Chromosomes:** method to exploit superposed states of qubits effectively, by
2. **Inference:** function to modify amplitudes of individuals to improve performance, by rotating the amplitudes of qubits in the chromosome.
3. **Qubit Rotation:** Quantum gates can be used to rotate amplitudes. (see equation 3 in paper)

- Paper continues with comparing the performances of a GA and QGA for the Knapsack Problem
- Results from the QGA performance show promise for work with problems requiring exploration of large search spaces.
## Citation
Laboudi, Z., & Chikhi, S. (2012). Comparison of genetic algorithm and quantum genetic algorithm. _Int. Arab J. Inf. Technol._, _9_(3), 243-249. [https://www.researchgate.net/publication/268381602_Comparison_of_Genetic_Algorithm_and_Quantum_Genetic_Algorithm]()

---
# Biased Random-Key Genetic Algorithm
Last Updated: 14 October 2026

Boxes are placed one at a time into the bins. A new bin opens if a box can't fit into bin already opened.
**Maximal-Space:** empty-space in bin that is not contained in other space in the bin. (Think $\rightarrow$ largest MaxRects $\rightarrow$ maximal rectangle)
Each chromosome represents box packing sequence.

**RKGA:** 
- chromosomes are vectors of randomly generated values that when decoded represent a combinatorial solution where fitness score can be computed.
- It is guaranteed that all offspring formed by crossover are feasible solutions.
- mutation: creates new vector random keys not influenced by elite individuals
- offspring solutions are created by crossover of elite individuals
**BRKGA:**
- mating occurs differently than in RKGA
	- one parent is from elite partition and another from entire population (both chosen randomly)
## Citation
The Modern Standard — Biased Random-Key Genetic Algorithm (BRKGA): Gonçalves, J. F., & Resende, M. G. C. (2011) — “A parallel biased random-key genetic algorithm for the two-dimensional and three-dimensional bin packing problems” (International Journal of Production Economics). [https://doi.org/10.1016/j.ejor.2024.03.030](https://doi.org/10.1016/j.ejor.2024.03.030)

---
# Polygon and Rectangle packing with Genetic Algorithms
Last Updated: 13 October 2026
## Summary
Jakobs approached the orthogonal packing problem by using a genetic algorithm.
**Proposed GA:**
- Underlying Algorithm: Bottom-Left Fit
	- Algorithm that fills board starting from the lower left corner.
	- Random permutation determine order in which rectangles are packed.
-  Fitness Function: Contiguous Area
	* A packing pattern resulting in the lowest height is desired. 
	* To do this we find the area of the contiguous remainder of each packing pattern, where a smaller contiguous remainder.
	$Area(ContiguousRemainder(PackingPattern)) = \sum_{k_i} |x^i_1-x^i_2|*(height(board)-y^i)$
	where $k_i = \{(x^i_1,y^1), (x^i_2,y^i)\}$
1. Initialization: 
	- Each individual in the population is defined by the permutation in which it is packed and its fitness value (which is determined in this step).
2. Selection:
	- Two individual are randomly selected for reproduction.
3. Crossover:
	- The offspring permutation is created by copying over a a subsequence in the permutation of parent 1 and the remaining permutation is filled by parent 2. 
4. Mutation:
	- rectangles of offspring are rotated at 90$\degree$ at a set probability. 
5. Elitism: 
	- individual with worst performing fitness value is replaced by offspring.
- Repeat steps 1 through 5 for set number iterations or until optimal packing pattern reached.

**Polygon Extension:**
(will write later...maybe)
## Points of Interest
- (when moving into rectilinear shape packing) consider clustering shapes (or embedding them into a rectangle) before packing rather than just utilizing rotations. 
## Citation
The Classic Sequence-Decoder GA: Jakobs, S. (1996) — “On genetic algorithms for the packing of polygons and rectangles” (Computer Methods in Applied Mechanics and Engineering). [https://doi.org/10.1016/0377-2217(94)00166-9](https://doi.org/10.1016/0377-2217\(94\)00166-9)

---
