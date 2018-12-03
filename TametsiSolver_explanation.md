# Summary

At its core, Tametsi is little more than solving a system of inequalities. For any given group of cells X, there is a minimum number Y and a maximum number Z of mines within that group of cells. By combining an given set of inequalities, starting with the row/column and color hints, further inequalities can be derived. Eventually, one gets so-called "trivial" inequalities where the number of mines in a group of cells is either 0 (so all of them can be revealed) or the same as the number of cells (so all of them are mines and should be flagged). After deriving these trivial inequalities, known inequalities can be adjusted and new inequalities can be created from newly-revealed hints. The difficulty in solving puzzles lies in combining inequalities to produce more.

# Core

As mentioned earlier, inequalities consist of three pieces of information:
* a set of cells, e.g. `{A, B, C, D}`,
* a minimum number of mines, e.g. 1, and
* a maximum number of mines, e.g. 3.

From here on, I will use `1 <= {A, B, C, D} <= 3` to represent this inequality. In fact, I'll go ahead and define some syntax to make talking about the rest of this easier. Given an inequality `X = (1 <= {A, B, C, D} <= 3)` and a similar inequality `Y = (2 <= {C, D, E} <= 2)`, then...
* `X.cells = {A, B, C, D}`, `X.min = 1`, and `X.max = 3`.
* `X + Y = UNION(X.cells, Y.cells)`, which is `{A, B, C, D, E}` in this case. For this and the following two operations, the bounds aren't considered since calculating those is considerably more complex and I want simple syntax to talk about various set operations on the cells.
* `X * Y = INTERSECTION(X.cells, Y.cells)`, which is `{C, D}` in this case.
* `X - Y = DIFFERENCE(X.cells, Y.cells)`, which is `{A, B}` in this case, and likewise, `Y - X = {E}`.
* `len(X)` is the number of cells in `X.cells`, which is `4` in this case.
* An inequality `X` is an **exact inequality** if and only if `X.min = X.max`.
* An inequality `X` is a **trivial inequality** if and only if `X.max = 0` *or* `X.min = len(X)`.

## Crossing Inequalities

Two inequalities `X` and `Y` can overlap in a variety of ways.
1. **Disjoint:** inequalities where there is no overlap between cell sets. These are simply not considered.
1. **Total overlap:** `X` and `Y` have the exact same set of cells. In such a case, the new minimum is then the maximum of `X.min` and `Y.min` and likewise, the new maximum is the minimum of maximums. Like disjoint inequalities, these are not normally considered.
1. **Subset:** `X` or `Y` is wholly contained within `Y` or `X`, respectively.
1. **Intersection:** `X` and `Y` have an overlap that is contained in but not equal to either `X` or `Y`.

Both the **subset** and **intersection** cases are special cases of a more general situation: `X` and `Y` have a non-empty overlap.

### Derived Inequalities

Crossing `X` and `Y` will produce two or three inequalities corresponding to `X * Y`, `X - Y`, and `Y - X`. Degenerate inequalities where the cell set is empty are not considered. I worked out these formulas by imagining shoving as many mines as possible into one subset or another.

**`Z = X * Y`**
* minimum: `max(0, X.min - (len(X) - len(Z)), Y.min - (len(Y) - len(Z)))` - putting as many of the mines in `X` or `Y` as possible into the cells not contained in `Z`.
* maximum: `min(len(Z), X.max, Y.max)` - putting as many of the mines in `X` or `Y` as possible into the cells contained in `Z`.

**`U = X - Y`** (also applies to **`V = Y - X`** but with `Y` instead of `X`)
* minimum: `max(0, X.min - Z.max)` - the mines in `X` minus the ones that can be put in `Z`.
* maximum: `min(len(U), max(0, X.max - Z.min))` - either all the cells in `U` are mines or it's the max number of mines in `X` minus the ones that have to be put in `Z`.

## Reducing Inequalities

# Improvements

* tiles encoded in binary
* exact inequalities
* inequality map

# Extensions

* record stage
* parent tracking