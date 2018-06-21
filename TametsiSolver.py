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
# import ipdb


def extend_unique(list1, list2):
  for x in list2:
    if x not in list1:
      list1.append(x)


class CellInequality(object):
  def __init__(self, cells, bounds, parents=None):
    if hasattr(cells, '__iter__'):
      temp = 0
      for x in cells:
        temp += 2 ** x
      cells = temp

    self.cells = cells
    self.num = bin(cells).count('1')
    self.set_bounds(bounds)
    self.set_parents(parents or [])

  def __repr__(self):
    return '({} with {})'.format(self.cell_nums, self.bounds)

  def set_bounds(self, bounds):
    if bounds[0] < 0 or bounds[1] < 0:
      raise ValueError("Cannot have negative bounds (bounds = {}).".format(bounds))
    if bounds[0] > bounds[1]:
      raise ValueError("Cannot have min greater than max (bounds = {}).".format(bounds))

    self.bounds = tuple(bounds)

  def set_parents(self, parents):
    self.parents = parents
    self.pedigree = [1] + [parent[0] for parent in parents]
    self.pedigree[0] = sum(self.pedigree)

  @property
  def trivial(self):
    return self.num == self.bounds[0] or self.bounds[1] == 0

  @property
  def exact(self):
    return self.bounds[0] == self.bounds[1]

  @property
  def cell_nums(self):
    nums = set()
    temp = self.cells

    i, j = 0, 1
    while j <= temp:
      if j & temp:
        nums.add(i)

      i, j = i + 1, j * 2

    return nums

  def isdisjoint(self, other):
    if not isinstance(other, CellInequality):
      raise ValueError("Other must be an inequality, not a {} (it is: {} )".format(type(other), other))

    return self.cells & other.cells == 0

  def issubset(self, other):
    if not isinstance(other, CellInequality):
      raise ValueError("Other must be an inequality, not a {} (it is: {} )".format(type(other), other))

    return self.cells & other.cells == self.cells

  def issuperset(self, other):
    if not isinstance(other, CellInequality):
      raise ValueError("Other must be an inequality, not a {} (it is: {} )".format(type(other), other))

    return self.cells & other.cells == other.cells

  def cross(self, other, max_cells=9, max_mines=3):
    if not isinstance(other, CellInequality):
      raise ValueError("Other must be an inequality, not a {} (it is: {} )".format(type(other), other))

    if self.cells == other.cells:
      return set()

    if self.isdisjoint(other):
      return set([self, other])

    if self.num > max_cells and self.bounds[0] > max_mines or other.num > max_cells and other.bounds[0] > max_mines:
      return set()

    shared_cells = self.cells & other.cells
    shared_num = bin(shared_cells).count('1')
    shared_bounds = (
      max(0, self.bounds[0] - self.num + shared_num, other.bounds[0] - other.num + shared_num),
      min(shared_num, self.bounds[1], other.bounds[1]),
    )

    new_ineqs = [CellInequality(shared_cells, shared_bounds, [self, other])]

    left_cells = self.cells & ~shared_cells
    if left_cells:
      left_bounds = (
        max(0, self.bounds[0] - shared_bounds[1]),
        min(self.num - shared_num, max(0, self.bounds[1] - shared_bounds[0])),
      )
      new_ineqs.append(CellInequality(left_cells, left_bounds, [self, other]))

    right_cells = other.cells & ~shared_cells
    if right_cells:
      right_bounds = (
        max(0, other.bounds[0] - shared_bounds[1]),
        min(other.num - shared_num, max(0, other.bounds[1] - shared_bounds[0])),
      )
      new_ineqs.append(CellInequality(right_cells, right_bounds, [self, other]))

    return new_ineqs


class CellSetDict(object):
  def __init__(self, cell_sets=None, ineq_map=None, strict=True):
    self.cell_set_map = dict()
    self.strict = strict

    if cell_sets and ineq_map:
      for cell_set in cell_sets:
        self.cell_set_map[cell_set] = ineq_map[cell_set]

    elif ineq_map:
      self.cell_set_map = ineq_map.copy()

    elif cell_sets and ineq_map is None:
      raise ValueError("If 'cell_sets' is provided, then 'ineq_map' must be provided as well.")

  def __bool__(self):
    return bool(self.cell_set_map)

  def __len__(self):
    return len(self.cell_set_map)

  def keys(self):
    return list(self.cell_set_map.keys())

  def values(self):
    return list(self.cell_set_map.values())

  def isdisjoint(self, other):
    return self.cell_set_map.keys().isdisjoint(other.cell_set_map.keys())

  def intersection(self, other):
    return [self.cell_set_map[key] for key in set(self.keys()).intersection(set(other.keys()))]

  def add_ineq(self, ineq, override=False):
    if ineq.cells in self.cell_set_map:
      old_ineq = self.cell_set_map[ineq.cells]

      if not override:
        if old_ineq.bounds == ineq.bounds:
          return

        new_bounds = (
          max(old_ineq.bounds[0], ineq.bounds[0]),
          min(old_ineq.bounds[1], ineq.bounds[1]),
        )
        old_ineq.set_bounds(new_bounds)

        extend_unique(old_ineq.parents, ineq.parents)
        old_ineq.set_parents(old_ineq.parents)

      else:
        old_ineq.set_bounds(ineq.bounds)
        old_ineq.set_parents(ineq.parents)

    else:
      self.cell_set_map[ineq.cells] = ineq

  def get_ineq(self, ineq_cells, strict=None):
    is_strict = strict is True or strict is None and self.strict is True

    if ineq_cells in self.cell_set_map:
      return self.cell_set_map[ineq_cells]
    elif is_strict:
      raise ValueError("No inequality found for cell set {}.".format(ineq_cells))

    return None

  def remove_ineq(self, ineq, strict=None):
    is_strict = strict is True or strict is None and self.strict is True

    if ineq is None:
      if is_strict:
        raise ValueError("Ineq must not be None if strict.")

    elif ineq.cells in self.cell_set_map:
      return self.cell_set_map.pop(ineq.cells)

    elif is_strict:
      raise ValueError("Cell set {} not found.".format(ineq.cells))

    return None

  def has_ineq(self, ineq, exact=True):
    if ineq.cells not in self.keys():
      return False

    else:
      retrieved = self.cell_set_map[ineq.cells]

      if exact:
        return retrieved.bounds == ineq.bounds

      else:
        return True

  def copy(self):
    return self.__class__(ineq_map=self.cell_set_map, strict=self.strict)


class InequalitySet(object):
  def __init__(self):
    self.ineqs = CellSetDict()
    self.roots = CellSetDict()
    self.fresh_ineqs = CellSetDict()

  def add(self, ineq, add_inexact=True):
    if add_inexact or ineq.exact:
      if not self.ineqs.has_ineq(ineq):
        self.ineqs.add_ineq(ineq)
        self.fresh_ineqs.add_ineq(ineq)

  def get(self, cells):
    return self.ineqs.get(cells, None)

  def remove(self, ineq):
    self.fresh_ineqs.remove_ineq(ineq, strict=False)
    return self.ineqs.remove_ineq(ineq, strict=False)

  def cross_all(self, add_inexact=True):
    if self.fresh_ineqs:
      ineqs_to_cross = self.fresh_ineqs
    else:
      print("Using 'em all.")
      ineqs_to_cross = CellSetDict(ineq_map=self.ineqs)

    before = len(self.ineqs)

    ineqs1 = sorted(ineqs_to_cross.values(), key=lambda x: x.num)
    ineqs2 = sorted(self.ineqs.values(), key=lambda x: x.num)

    for ineq1 in ineqs1:
      # print("ineq1:", ineq1)
      for ineq2 in ineqs2:
        if ineq2.cells < ineq1.cells:
          continue

        for new_ineq in ineq1.cross(ineq2):
          self.add(new_ineq, add_inexact)

    after = len(self.ineqs)
    if before != after:
      self.fresh_ineqs = CellSetDict()

  def purge(self, filter_func):
    for ineq in self.ineqs.values():
      if filter_func(ineq):
        self.remove(ineq)

  def find_trivial(self):
    trivial_ineqs = []

    for ineq in sorted(self.ineqs.values(), key=lambda x: x.num, reverse=True):
      if ineq.trivial:
        for trivial in trivial_ineqs:
          if ineq.issubset(trivial):
            break
        else:
          trivial_ineqs.append(ineq)

    return trivial_ineqs

  def reduce(self, trivial_ineqs):
    revealed = set()
    flagged = set()

    for trivial in trivial_ineqs:
      if trivial.bounds[0] == 0:
        revealed = revealed.union(trivial.cell_nums)

      elif trivial.bounds[0] > 0:
        flagged = flagged.union(trivial.cell_nums)

    marked = revealed.union(flagged)
    print("marked:", marked)

    for ineq in sorted(self.ineqs.values(), key=lambda x: x.num, reverse=True):
      # ipdb.set_trace()
      if ineq.cell_nums.issubset(marked):
        # print("issubset")
        self.remove(ineq)

      elif not marked.isdisjoint(ineq.cell_nums):
        # print("not disjoint", ineq)
        self.remove(ineq)
        num_flagged = len(flagged.intersection(ineq.cell_nums))

        new_cells = ineq.cell_nums.difference(marked)
        new_bounds = (
          min(max(ineq.bounds[0] - num_flagged, 0), len(new_cells)),
          min(ineq.bounds[1] - num_flagged, len(new_cells)),
        )

        self.add(CellInequality(new_cells, new_bounds, [ineq]))


class Puzzle(object):
  def __init__(self, board, revealed, constraints):
    self.board = board
    self.revealed = revealed
    self.ineq_set = InequalitySet()
    self.constraints = self.convert_constraints(constraints)
    self.flagged = []
    self.newly_revealed = []
    self.newly_flagged = []
    self.rounds = []

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
    for c in self.newly_revealed:
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

    self.newly_revealed = []

  def record_stage(self, func, *args, **kwargs):
    name = func.__name__
    before = len(self.ineq_set.ineqs)
    print("before {} (with args {} and kwargs {}): {}".format(name, args, kwargs, before))

    func(*args, **kwargs)

    after = len(self.ineq_set.ineqs)
    print("after {} (with args {} and kwargs {}): {}".format(name, args, kwargs, after))
    diff = after - before
    self.rounds[-1][name] = [before, after, diff]

    return diff

  def solve_puzzle(self):
    self.newly_revealed = self.revealed[:]
    total_diff = 1

    while self.ineq_set.ineqs and total_diff > 0:
      self.rounds.append({})
      total_diff = 0

      total_diff += abs(self.record_stage(self.make_new_inequalities))
      total_diff += abs(self.record_stage(self.ineq_set.cross_all, add_inexact=False))

      if total_diff > 0:
        self.record_stage(self.ineq_set.purge, lambda x: not x.exact)
      else:
        total_diff += abs(self.record_stage(self.ineq_set.cross_all, add_inexact=True))

      trivial_ineqs = self.ineq_set.find_trivial()

      for trivial in trivial_ineqs:
        if trivial.bounds[0] == 0:
          # all cells revealed
          revealed_cells = trivial.cell_nums
          extend_unique(self.revealed, revealed_cells)
          extend_unique(self.newly_revealed, revealed_cells)

        elif trivial.bounds[0] > 0:
          # all cells flagged
          flagged_cells = trivial.cell_nums
          extend_unique(self.flagged, flagged_cells)
          extend_unique(self.newly_flagged, flagged_cells)

      self.rounds[-1]['trivial'] = [self.newly_revealed[:], self.newly_flagged[:], trivial_ineqs[:]]

      print("\n trivial")
      print(trivial_ineqs)

      total_diff += abs(self.record_stage(self.ineq_set.reduce, trivial_ineqs))

      print()
      print("Revealed:", self.revealed)
      print("Flagged:", self.flagged)
      print("Newly revealed:", self.newly_revealed)
      print("Newly flagged:", self.newly_flagged)
      print()

    return (self.revealed, self.flagged, self.ineq_set.ineqs)


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

  level = 6

  if level == 1:
    # Combination Lock I
    # . * . ? . .
    # . * . ? . .
    # * . * * * ?
    # * * . ? . .
    # * ? * . * .
    # . . . * . ?
    compressed = '.*.?...*.?..*.***?**.?..*?*.*....*.?'
    w, h = 6, 6

  elif level == 2:
    # Combination Lock II
    # . * * * . *
    # . . * * * *
    # * . * . . *
    # . ? . . . .
    # . * . . * ?
    # . * . * * *
    compressed = '.***.*..*****.*..*.?.....*..*?.*.***'
    w, h = 6, 6

  elif level == 6:
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
  pprint.pprint(constraints, width=160)

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
    else:
      raise
