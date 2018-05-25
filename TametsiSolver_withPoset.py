"""
A solver for Tametsi-like puzzles that works by resolving chains of inequalities.

Assumptions/conditions:

* Cells either have or do not have a mine and they are either a tile or revealed/flagged (no mine/mine respectively).
* If a cell is revealed, it has either a non-negative integer denoting the number of neighboring cells with mines, or a ? representing an unknown count.
* Column and color hints also exist that assert a given group of cells have some non-negative integer of mines.

* Inequalities have 1) a set of N cells and 2) 0 <= lower bound <= upper bound <= N for the number of mines in them.
* Inequalities are constructed from column/color hints and revealed cells.
* Additional inequalities may be derived by splitting and combining prior inequalities.
* Important: when combining inequalities, one will always be contained in the other.
* Derived inequalities are never any larger than the "parent" inequalities.

* Inequalities where lower bound == N ("full") or upper bound == 0 ("empty") are trivial.
* Trivial inequalities are eliminated and inequalities that depend on them need to be adjusted and/or re-derived.
* Full inequalities result in all contained tiles being flagged and related inequalities adjusted.
* Empty inequalities result in all contained tiles being revealed, related inequalities adjusted, and potentially new inequalities constructed.

* A solution is found when all cells have been flagged or revealed.
* Revealing a mine means immediate failure.
"""

import sys
import IPython
import pprint


class CellInequality(object):
  def __init__(self, cells, bounds):
    self.cells = frozenset(cells)
    self.bounds = tuple(bounds)

    if self.bounds[0] < 0 or self.bounds[1] < 0:
      raise ValueError("Cannot have negative bounds (self = {}).".format(self))
    if self.bounds[0] > self.bounds[1]:
      raise ValueError("Cannot have min greater than max (self = {}).".format(self))

  @property
  def id(self):
    return (self.cells, self.bounds)

  def __eq__(self, other):
    if not isinstance(other, CellInequality):
      return False
    else:
      return self.id == other.id

  def __hash__(self):
    return hash(self.id)

  def __repr__(self):
    return '({} with {})'.format(set(self.cells), self.bounds)
  # __repr__ = __str__

  @property
  def trivial(self):
    return len(self.cells) == self.bounds[0] or self.bounds[1] == 0

  def split(self):
    if len(self.cells) > 9:
      return set()

    cell_sets = [set()]

    for x in self.cells:
      for i in range(len(cell_sets)):
        cell_sets.append(cell_sets[i].union({x}))

    split_ineqs = set()
    for cell_set in cell_sets[1:-1]:
      new_bounds = [
        max(0, self.bounds[0] - (len(self.cells) - len(cell_set))),
        min(len(cell_set), self.bounds[1]),
      ]

      split_ineqs.add(CellInequality(cell_set, new_bounds))

    return split_ineqs

  def combine(self, other):
    if not isinstance(other, CellInequality):
      return set()

    # ineq1 is a subset of ineq2
    if self.cells.issubset(other.cells):
      ineq1 = self
      ineq2 = other
    elif self.cells.issuperset(other.cells):
      ineq1 = other
      ineq2 = self
    else:
      return set()

    if len(ineq1.cells) > 19:
      return set()
    if len(ineq2.cells) > 19:
      return set()

    # bounds for subset might change
    subset_bounds = [
      max(ineq1.bounds[0], ineq2.bounds[0] - (len(ineq2.cells) - len(ineq1.cells))),
      min(ineq1.bounds[1], ineq2.bounds[1]),
    ]
    subset = CellInequality(ineq1.cells, subset_bounds)

    if ineq1.cells == ineq2.cells:
      return {subset}

    # bounds for complement
    comp_bounds = [
      max(0, ineq2.bounds[0] - subset.bounds[1]),
      min(len(ineq2.cells) - len(subset.cells), max(0, ineq2.bounds[1] - subset.bounds[0])),
    ]
    comp = CellInequality(ineq2.cells.difference(subset.cells), comp_bounds)

    return {subset, comp}


class InequalitySet(object):
  def __init__(self):
    self.ineqs = dict()
    self.fresh_ineqs = set()
    self.fresh_splits = set()

  def add(self, ineq):
    cells = ineq.cells

    if cells in self.ineqs:
      new_bounds = (
        max(self.ineqs[cells].bounds[0], ineq.bounds[0]),
        min(self.ineqs[cells].bounds[1], ineq.bounds[1]),
      )
      ineq = CellInequality(cells, new_bounds)

    self.ineqs[cells] = ineq
    self.fresh_ineqs.add(cells)

  def get(self, cells):
    return self.ineqs.get(cells, None)

  def remove(self, ineq_cells):
    if ineq_cells in self.fresh_ineqs:
      self.fresh_ineqs.remove(ineq_cells)
    return self.ineqs.pop(ineq_cells, None)

  def split_ineqs(self):
    self.fresh_splits = set()

    if self.fresh_ineqs:
      ineqs_to_split = self.fresh_ineqs
    else:
      ineqs_to_split = self.ineqs.keys()
    # ineqs_to_split = self.ineqs.keys()

    for ineq_cells in list(ineqs_to_split):
      self.fresh_splits.add(ineq_cells)
      for split in self.ineqs[ineq_cells].split():
        self.add(split)
        self.fresh_splits.add(split.cells)

    self.fresh_ineqs = set()

  def combine_ineqs(self):
    if self.fresh_splits:
      splits_cells = self.fresh_splits
    else:
      splits_cells = self.ineqs.keys()
    # splits_cells = self.ineqs.keys()

    for split_cells in splits_cells:
      split = self.ineqs[split_cells]
      for ineq in list(self.ineqs.values()):
        if ineq.cells != split_cells:
          for comb in ineq.combine(split):
            self.add(comb)

  def find_trivial(self):
    trivial_ineqs = []

    for ineq in sorted(self.ineqs.values(), key=lambda x: len(x.cells), reverse=True):
      if ineq.trivial:
        for trivial in trivial_ineqs:
          if ineq.cells.issubset(trivial.cells):
            break
        else:
          trivial_ineqs.append(ineq)

    return trivial_ineqs

  def reduce(self, trivial_ineqs):
    revealed = set()
    flagged = set()

    for trivial in trivial_ineqs:
      if trivial.bounds[0] == 0:
        revealed = revealed.union(trivial.cells)

      elif trivial.bounds[0] > 0:
        flagged = flagged.union(trivial.cells)

    marked = revealed.union(flagged)

    # if not marked: import ipdb; ipdb.set_trace()

    for ineq in list(self.ineqs.values()):
      for trivial in trivial_ineqs:
        if ineq.cells.issubset(marked):
          self.remove(ineq.cells)

        elif not marked.isdisjoint(ineq.cells):
          self.remove(ineq.cells)
          num_flagged = len(flagged.intersection(ineq.cells))

          new_cells = ineq.cells.difference(marked)
          new_bounds = (
            min(max(ineq.bounds[0] - num_flagged, 0), len(new_cells)),
            min(ineq.bounds[1] - num_flagged, len(new_cells)),
          )

          self.add(CellInequality(new_cells, new_bounds))


class Puzzle(object):
  def __init__(self, board, revealed, constraints):
    self.board = board
    self.revealed = revealed
    self.ineq_set = InequalitySet()
    self.constraints = self.convert_constraints(constraints)
    self.flagged = []
    self.changed = []

  def convert_constraints(self, constraints):
    for constraint in constraints:
      cells = []
      count = constraint[0]

      for c in constraint[1]:
        if c not in self.revealed:
          cells.append(c)

      if cells:
        self.ineq_set.add(CellInequality(cells, (count, count)))

  def make_new_inequalities(self):
    for c in self.changed:
      if self.board[c][1] == '.':
        cells = []
        count = 0

        for i in self.board[c][2]:
          if i not in self.flagged + self.revealed:
            cells.append(i)

            if self.board[i][1] == '*':
              count += 1

        if cells:
          self.ineq_set.add(CellInequality(cells, (count, count)))

    self.changed = []

  def extend_unique(self, list1, list2):
    for x in list2:
      if x not in list1:
        list1.append(x)

  def solve_puzzle(self):
    self.changed = self.revealed[:]

    while self.ineq_set.ineqs:

      self.make_new_inequalities()
      self.ineq_set.split_ineqs()
      self.ineq_set.combine_ineqs()

      trivial_ineqs = self.ineq_set.find_trivial()

      for trivial in trivial_ineqs:
        if trivial.bounds[0] == 0:
          # all cells revealed
          revealed_cells = sorted(list(trivial.cells))
          self.extend_unique(self.revealed, revealed_cells)
          self.extend_unique(self.changed, revealed_cells)

        elif trivial.bounds[0] > 0:
          # all cells flagged
          flagged_cells = sorted(list(trivial.cells))
          self.extend_unique(self.flagged, flagged_cells)

      self.ineq_set.reduce(trivial_ineqs)

      print()
      print("Revealed:", self.revealed)
      print("Flagged:", self.flagged)
      print("Changed:", self.changed)
      print()

      # import ipdb; ipdb.set_trace()

    return (self.revealed, self.flagged, self.ineq_set.ineqs)

  def print_progress(self):
    pass


def demo1():
  # . * . *
  # ? . . ?
  board = [
    (0, '.', (1, 4, 5)),
    (1, '*', (0, 2, 4, 5, 6)),
    (2, '.', (1, 3, 5, 6, 7)),
    (3, '*', (2, 6, 7)),
    (4, '?', (0, 1, 5)),
    (5, '.', (0, 1, 2, 4, 6)),
    (6, '.', (1, 2, 3, 5, 7)),
    (7, '?', (2, 3, 6)),
  ]
  revealed = [0, 5, 7]
  constraints = [
    (2, [0, 1, 2, 3, 4, 5, 6, 7]),
  ]

  print('board:', board)
  print('constraints:', constraints)

  print(Puzzle(board, revealed, constraints).solve_puzzle())


def demo2():
  # Combination Lock levels

  # # Combination Lock I
  # # . * . ? . .
  # # . * . ? . .
  # # * . * * * ?
  # # * * . ? . .
  # # * ? * . * .
  # # . . . * . ?
  # compressed = '.*.?...*.?..*.***?**.?..*?*.*....*.?'
  # w, h = 6, 6

  # # Combination Lock II
  # # . * * * . *
  # # . . * * * *
  # # * . * . . *
  # # . ? . . . .
  # # . * . . * ?
  # # . * . * * *
  # compressed = '.***.*..*****.*..*.?.....*..*?.*.***'
  # w, h = 6, 6

  # Combination Lock VI
  # * * ? . . . . * * .
  # * . . . * . * . . .
  # . . . * . . . . . .
  # * . * . ? * * . * .
  # * * ? . * ? ? . . .
  # . * * . ? * . ? ? .
  # . . . . * . * * * .
  # . . . . . . . . . .
  # * ? * * . * . . . *
  # * . * ? . . * * ? .
  compressed = '**?....**.*...*.*......*......*.*.?**.*.**?.*??....**.?*.??.....*.***...........*?**.*...**.*?..**?.'
  w, h = 10, 10

  board = []

  for i in range(w * h):
    neighbors = []
    board.append((i, compressed[i], neighbors))

    for dx in [-1, 0, 1]:
      if i % w + dx < 0 or i % w + dx >= w:
        continue

      for dy in [-1, 0, 1]:
        if i // w + dy < 0 or i // w + dy >= h:
          continue

        if [dx, dy] == [0, 0]:
          continue

        neighbors.append(i + dx + w * dy)

  constraints = [(compressed.count('*'), list(range(w * h)))]

  # vertical column hints
  for j in range(w):
    constraints.append((
      compressed[j::w].count('*'),
      [j + k * w for k in range(h)],
    ))

  # horizontal column hints
  for j in range(h):
    constraints.append((
      compressed[j * w:j * w + w].count('*'),
      list(range(j * w, j * w + w)),
    ))

  revealed = []

  print('board:', board)
  print('constraints:')
  pprint.pprint(constraints)

  print(Puzzle(board, revealed, constraints).solve_puzzle())


def demo3():
  # 53: Squared Square
  board = [
    (0, '?', (1, 3, 5, 6)),
    (1, '?', (0, 2, 3, 4)),
    (2, '?', (1, 4, 7, 8)),
    (3, '*', (0, 1, 2, 4, 6, 7, 9, 10)),
    (4, '.', (1, 2, 3, 7)),
    (5, '.', (0, 6, 9, 13)),
    (6, '?', (0, 3, 5, 9)),
    (7, '.', (2, 3, 4, 8, 10, 11, 12)),
    (8, '.', (2, 7, 12, 15)),
    (9, '.', (3, 5, 6, 10, 11, 13, 14)),
    (10, '?', (3, 7, 9, 11)),
    (11, '.', (7, 9, 10, 12, 14, 15, 16)),
    (12, '*', (7, 8, 11, 15)),
    (13, '*', (5, 9, 14, 16)),
    (14, '?', (9, 11, 13, 16)),
    (15, '?', (8, 11, 12, 16)),
    (16, '.', (11, 13, 14, 15)),
  ]
  revealed = [10, 11, 16]
  constraints = [
    (1, [0, 2, 13, 15]),  # pink
    (0, [1, 5, 8, 16]),  # red
    (1, [3, 7, 9, 11]),  # orange
    (1, [4, 6, 10, 12, 14]),  # yellow
    (3, list(range(17))),  # total
  ]

  print('board:', board)
  print('constraints:', constraints)

  print(Puzzle(board, revealed, constraints).solve_puzzle())


if __name__ == "__main__":
  repl = 'repl' in sys.argv

  demos = {
    '1': demo1,
    '2': demo2,
    '3': demo3,
  }

  try:
    if len(sys.argv) > 1:
      n = sys.argv[1]
      if n in demos:
        demos[n]()

    if repl:
      IPython.embed()
  except Exception:
    if repl:
      IPython.embed()
