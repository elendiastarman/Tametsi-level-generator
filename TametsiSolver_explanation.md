# Summary

At its core, Tametsi is little more than solving a system of inequalities. For any given group of cells X, there is a minimum number Y and a maximum number Z of mines within that group of cells. By combining an given set of inequalities, starting with the row/column and color hints, further inequalities can be derived. Eventually, one gets so-called "trivial" inequalities where the number of mines in a group of cells is either 0 (so all of them can be revealed) or the same as the number of cells (so all of them are mines and should be flagged). After deriving these trivial inequalities, known inequalities can be adjusted and new inequalities can be created from newly-revealed hints. The difficulty in solving puzzles lies in combining inequalities to produce more.

# Core

As mentioned earlier, inequalities consist of three pieces of information:
* a set of cells, e.g. `{A, B, C, D}`,
* a minimum number of mines, e.g. 1, and
* a maximum number of mines, e.g. 3.

From here on, I will use `1 <= {A, B, C, D} <= 3` to represent this inequality. In fact, I'll go ahead and define some syntax to make talking about the rest of this easier. Given an inequality `X = (1 <= {A, B, C, D} <= 3)` and a similar inequality `Y = (2 <= {C, D, E} <= 2)`, then...
* `X.cells = {A, B, C, D}`, `X.min = 1`, and `X.max = 3`.
* 

## Crossing Inequalities

Two inequalities `X` and `Y` can overlap in a variety of ways.
1. **Disjoint:** inequalities where there is no overlap between cell sets. These are simply not considered.
1. **Total overlap:** `X` and `Y` have the exact same set of cells. In such a case, the new minimum is then the maximum of `X.min` and `Y.min` and likewise, the new maximum is the minimum of maximums.
1. **Subset:** `X` or `Y` is wholly contained within `Y` or `X`, respectively.
1. **Intersection:** `X` and `Y` have an overlap that is contained in but not equal to either `X` or `Y`.

### Subset

### Intersection

## Reducing Inequalities

# Improvements

* tiles encoded in binary
* exact inequalities
* inequality map

# Extensions

* record stage
* parent tracking