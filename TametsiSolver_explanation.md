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

Once trivial inequalities have been found and the corresponding tiles revealed or flagged, it's time to adjust inequalities that overlap with any trivial inequality. The sets of newly revealed and newly flagged tiles are calculated and every existing inequality is checked to see how much they overlap with these two sets. 

# Improvements

## Tiles Encoded As Binary

Originally, tiles were tracked in `set` objects. Operations involving sets, such as unions, intersections, and differences, are comparatively slow in Python. Conveniently, Python's native biginteger support meant that I could encode the tiles in an inequality as a binary number where each digit was a 1 to indicate that tile was in the set and 0 otherwise. Thus, unions become binary OR, intersections become binary AND, and differences become binary AND NOT. In Python operations, these are `X & Y`, `X | Y`, and `X & ~Y`. This conferred quite a significant speedup, which makes sense; binary operations are usually pretty optimized already.

## Exact Inequalities

An "exact" inequality is one where a given inequality `X` has `X.min == X.max`. As it turns out, exact inequalities are somehow quite useful. Generally, working *only* with exact inequalities confers a massive speed improvement, largely because there aren't as many that can be derived from a given set of inequalities. However, they are not *sufficient* to deduce every logic step of all puzzles. For example, Combination Lock VI has one step that requires deriving inexact inequalities. Hence, for every step, exact inequalities are derived first and then if no progress is made, inexact inequalities are derived. Leaving these inexact inequalities around slows down the solver quite a bit because there's so many of them. Hence, so immediately after any cells are revealed or flagged, all inexact inequalities are deleted.

My solver allows you to configure the number of allowed "inexact rounds", so to speak, that specifies the maximum number of consecutive rounds that have to use inexact inequalities. The counter resets every time inexact inequalities are purged, so it's possible to have the max number of inexact rounds be 1 and still have three such rounds in a puzzle; they just can't be consecutive. I have found that setting this max to 1 produces relatively good puzzles; fewer than that tends to produce easier puzzles and more than that tends to produce weaker/messier puzzles and/or make them less satisfying to solve.

## Inequality Map

Realistically, any given set of tiles has at most one known inequality. Hence, the solver maintains a mapping from the tiles in an inequality to the min and max of that inequality. If a new inequality is derived that has the same tiles as one already known, then that means both can be replaced with a more accurate inequality that takes both pairs of bounds into account. That is, if `X.cells == Y.cells`, then (calling the new one `Z` for convenience) `Z.min = max(X.min, Y.min)` and `Z.max = min(X.max, Y.max)`.

# Extensions

* record stage
* parent tracking

# Scoring

Scoring a puzzle is actually rather difficult. Rating the difficulty of a puzzle is already a rather subjective experience for humans, let alone an algorithm. Thus far, I've only experimented with scoring methods that look at the number of rounds it took to deduce each logical step. In general, the more rounds it took, the harder it is to make that logical deduction. Most of the time, it takes just 1 round, but I have seen them go as high as 7, though that is of course quite rare.

## Smooth Difficulty

I initially scored my puzzles very simply: just look at how many of each difficulty level there are. I later developed a different scoring algorithm that attempts to optimize for "smoothness" in the difficulty curve. So [1, 3, 3, 1] should be better than [1, 5, 1, 1].

Excepting unsolvable and trivial puzzles, the smooth difficulty score is calculated by taking every adjacent pair of steps `a, b`, calculating intermediate scores, and then summing them up. The intermediate score for a given pair of steps `a, b` is calculated by setting `x = min(a, b)` and `y = max(a, b)` and then calculating `x * (y - 1) / (y - x + 1)`. The intent is to reward similarity between `a` and `b` as well as rewarding higher values for them.

Let's suppose a given puzzle has steps of difficulty [1, 3, 2, 1, 3, 1]. Then the pairs and intermediate scores are as follows:

```
1, 3 -> 1 * (3 - 1) / (3 - 1 + 1) = 2 / 3 ~= 0.667
3, 2 -> 2 * (3 - 1) / (3 - 2 + 1) = 4 / 2 ~= 2.0
2, 1 -> 1 * (2 - 1) / (2 - 1 + 1) = 1 / 2 ~= 0.5
1, 3 ~= 0.667
3, 1 ~= 0.667
```

Which sums up to about 4.5 altogether.

Now let's suppose it instead had difficulty steps of [1, 1, 6, 1, 1].

```
1, 1 -> 1 * (1 - 1) / (1 - 1 + 1) = 0
1, 1 = 0
1, 6 -> 1 * (6 - 1) / (6 - 1 + 1) = 5 / 5 = 1
1, 1 = 0
1, 1 = 0
```

Which sums up to 1 altogether.

So a puzzle that has a few medium difficulty steps will score much higher than a puzzle that just has one really hard step. My intent is that this produces puzzles that are more enjoyable to play given that the difficulty curve tends to be a bit more level.
