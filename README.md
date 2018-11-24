# Tametsi-level-generator
Code for generating Tametsi levels

Example usage:

```
# Solves a demo puzzle (Combination Lock 6 from the main game)
python TametsiSolver.py 2

# Generates 8x8 combination lock puzzles
python TametsiGenerator.py 8 8

# Takes a compressed string and turns it into a Tametsi level file (Combination Lock I from the main game)
python TametsiWriter.py 6 6 ".*.?...*.?..*.***?**.?..*?*.*....*.?"
```