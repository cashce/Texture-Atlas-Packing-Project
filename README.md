# Texture Atlas Packing Project
## Overview
This project aims to showcase various algorithms for texture atlas packing.

## Current Features
### Recently Added
* function for sorting textures based on area, perimeter, shortest side, and longest side
* Skyline, Guillotine, and MaxRects algorithms all support 90 degree rotations of rectangles 
* visualization function of the packed atlas that supports generated shapes and imported texture files
### Older Features
* Skyline packing algorithm
* Guillotine packing algorithm
* MaxRects packing algorithm
* shape generator class for creating rectangles for testing packing algorithms
* greedy packing algorithm that packs rectangular textures into an atlas by starting in the top left corner of the atlas and packing following objects into the next position available
* empty space calculation for packed atlas

## Future Features
* multiple heuristics for packing algorithms
* implementation of a genetic algorithm for atlas packing
* support for packing rectilinear polygons
