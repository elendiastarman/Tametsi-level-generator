# Tametsi Level Generator

### [How to Run](#how-to-run) or [How to Use](#how-to-use)

## How to Run

* [Individual parts](#individual-parts)
* [Example invocation](#example-invocation)
* [Example output](#example-output)
* [Playing in Tametsi](#playing-in-tametsi)

### Individual parts:

There are three major parts runnable from the command line:

* Generator - `python generator.py <template_name> <scoring_method> [arg1] [arg2] [...]` - generates random puzzles based on the referenced template and, after solving them, scores them (-1 if it failed, non-negative otherwise). It periodically prints the hardest puzzle seen so far.
* Writer - `python writer.py <template_name> <compressed> [arg1] [arg2] [...]` - takes a template name, a compressed string representing the puzzle's mine layout, and (likely) some number of arguments to produce a puzzle file that can be loaded by Tametsi.
* Tester - `python test.py [puzzle_id [--verbose]]` - runs the scorer on one or all of the puzzle files in `/test` to validate them and compute scores (along with how long it took to solve).

### Example invocation:

All together, this looks something like:

```bash
python generator.py combination_lock seqnum 3
# .*?*?.?.*
# ??..**?.*
# etc
python writer.py combination_lock .*?*?.?.* 3
python test.py 161

cat test/index
# 101 2018_01_15_A.puz
# <snip>
# 161 latest.puz
```

### Example output:

```
✗ python generator.py combination_lock seqnum 6                                    
argv: ['generator.py', 'combination_lock', 'seqnum', '6']                   
Best of round 1: ?..***.*..*??*?..*?...*.?****?.??.*? with score 13 and steps TEETETTETETTTETTTTTT
 ^ Best so far!
Best of round 2: *...???.*...*..*.***.*?....?....*.*. with score 24 and steps TEEEETEETTETTTTTTTTTTT
 ^ Best so far!
 Best of round 10: *.?*....*?*.....*?..??..?**.?*?*..** with score 21 and steps TETEETTEETEETETTETTTTTTT
 ^ Best so far!
Best of round 14: *....*.**.?....***.?.....**.......*. with score 31 and steps TEETEEEETETTEETTETTTTT
 ^ Best so far!

✗ python writer.py combination_lock "*....*.**.?....***.?.....**.......*." 6       
puzzles/20210930_Combination-Lock-6x6-with-score-31.puz

✗ python tester.py -1
filenames: ['../latest.puz']
  1 ../latest.puz       : 0.046 seconds, solved True, score 31.000 - Combination Lock 6x6 with score 31
```

### Playing in Tametsi

Tametsi actually has a built-in method of loading additional puzzle files - that's how the bonus levels 101-160 are loaded! They're in `/puzzles` within the root Tametsi folder (likely `/your/path/to/SteamLibrary/steamapps/common/Tametsi`). On game startup, Tametsi reads all `.puz` files in this folder and displays them on the in-game selection screen. Simply put your newly-generated puzzles in that folder and reboot the game!

## How to Use

There are a few more major parts that the above scripts use to do their dirty work.

* Solver - `solver.py` - the `Puzzle` class is constructed from a neighbor graph, a starting set of revealed cells, and all constraints. `puzzle.solve()` then performs arcane magics and (potentially) out comes a solution! The general structure of the solution is a list of cells successfully revealed or flagged per solver round.
* Templater - `templater.py` - defines a set of pairs of `<template_name>` (internal puzzle data) and `<template_name>_render` (Tametsi puzzle file format) functions that take some parameters and produce a puzzle template.
* Scorer - `scorer.py` - defines scoring functions that take the solution of a puzzle and compute a non-negative numerical score from it.
* Loader - `loader.py` - The `load` function takes a puzzle file and parses it much like Tametsi would to produce a `Puzzle` instance that can then be `.solve`d.

## Extra Stuff

The keen-eyed among you will have noticed `game_puzzles` in the repo. This is a symbolic link (symlink) to Tametsi's root directory, in this case to the Steam folder for the game. The beginning of it will change depending on which platform you're running this on, but the ending should be pretty consistent. At worst, just google "how to find Steam game folder". :) Anyway, this symlink enables you to copy files from the repo root to the game's `puzzles` directory with ease for immediate testing in-game. (You have to relaunch the game every time you want to load a new file.)

I wrote [a high-level explanation of how this solver works](/TametsiSolver_explanation.md) because that's the legitimately-hard part. *It took me **months** to get the solver fast enough to use.* T_T

## Future Plans

I would love to figure out some way to run a GUI with Python (or perhaps a mini webpage :thinking:) that makes it easy to create levels like those in Tametsi, and then export them in a format that can be understood by the solver, thereby enabling a true level generator for the game. (I have no intent to make it anywhere near pretty enough to compete with the actual game, so it'll just be really basic stuff.)
