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


def cells_to_binary(cells):
  num = 0
  for x in cells:
    num += 2 ** x
  return num


def binary_to_cells(num):
  cells = set()

  i, j = 0, 1
  while j <= num:
    if j & num:
      cells.add(i)

    i, j = i + 1, j * 2

  return cells


class Puzzle(object):
  def __init__(self, board, revealed, constraints, verbose=False, max_inexact_stages=-1):
    self.board = board
    self.revealed = revealed
    self.constraints = self.convert_constraints(constraints)
    self.verbose = verbose
    self.max_inexact_stages = max_inexact_stages

    self.flagged = []
    self.newly_revealed = []
    self.newly_flagged = []
    self.rounds = []

  def convert_constraints(self, constraints):
    converted = []

    for constraint in constraints:
      cells = []
      count = constraint[0]

      for c in constraint[1]:
        if c not in self.revealed:
          cells.append(c)

      if cells:
        converted.append([cells_to_binary(cells), count, count, len(cells)])

    return converted

  def index_add_remove(self, index, action, num):
    n = 1
    while n <= num:
      if n & num:

        if action == 'add':
          index.setdefault(n, set()).add(num)
        elif action == 'remove':
          if n in index and num in index[n]:
            index[n].remove(num)

      n *= 2

  def group_add_remove(self, groups, action, num, exact):
    if exact:
      target = [
        groups['fe_fe'],
        groups['fe_fi']['exact'],
        groups['fe_se']['fresh'],
        groups['fe_si']['fresh'],
      ]
      if action == 'remove' and num in groups['fe_se']['stale']:
        groups['fe_se']['stale'].remove(num)

    else:
      target = [
        groups['fi_fi'],
        groups['fi_se']['fresh'],
        groups['fi_si']['fresh'],
      ]
      if action == 'remove' and num in groups['fe_fi']['inexact']:
        groups['fe_fi']['inexact'].remove(num)
        groups['fi_si']['stale'].remove(num)

    for group in target:
      if action == 'add':
        group.add(num)
      elif action == 'remove' and num in group:
        group.remove(num)

  def add_ineq(self, to_add, ineqs, groups):
    num = to_add[0]
    known = ineqs.get(num, None)
    old = None

    if known:
      if known[0] >= to_add[1] and known[1] <= to_add[2]:
        return known, False

      old = known[:]
      new_min = max([known[0], to_add[1]])
      new_max = min([known[1], to_add[2]])
      known[0] = new_min
      known[1] = new_max

    else:
      known = ineqs[num] = to_add[1:]

    if old:
      self.group_add_remove(groups, 'remove', num, old[0] == old[1])

    if known[1] == 0 or known[0] == known[2]:
      groups['trivial'].add(num)

    self.group_add_remove(groups, 'add', num, known[0] == known[1])
    return known, True

  def pop_ineq(self, to_pop, ineqs, groups):
    known = ineqs.pop(to_pop, None)

    if known:
      self.group_add_remove(groups, 'remove', to_pop, known[0] == known[1])

    return known

  def cross_ineqs(self, left, left_bounds, right, right_bounds):
    to_add = []

    shared_num = left & right
    shared_count = bin(shared_num).count('1')
    shared_bounds = [
      max(0, left_bounds[0] - left_bounds[2] + shared_count, right_bounds[0] - right_bounds[2] + shared_count),
      min(shared_count, left_bounds[1], right_bounds[1]),
    ]
    to_add.append([shared_num] + shared_bounds + [shared_count])

    nleft_num = left & ~right
    if nleft_num:
      nleft_bounds = [
        max(0, left_bounds[0] - shared_bounds[1]),
        min(left_bounds[2] - shared_count, max(0, left_bounds[1] - shared_bounds[0])),
        bin(nleft_num).count('1'),
      ]
      to_add.append([nleft_num] + nleft_bounds)

    nright_num = ~left & right
    if nright_num:
      nright_bounds = [
        max(0, right_bounds[0] - shared_bounds[1]),
        min(right_bounds[2] - shared_count, max(0, right_bounds[1] - shared_bounds[0])),
        bin(nright_num).count('1'),
      ]
      to_add.append([nright_num] + nright_bounds)

    return to_add

  def cross_all_pairs(self, lefts, rights, ineqs, groups, max_cells=9, max_mines=3):
    any_added = False
    eliminated = set()

    for left in lefts:
      eliminated.add(left)

      left_bounds = ineqs.get(left)
      if self.verbose:
        print(f'left: {binary_to_cells(left), left_bounds}')
        out2 = None

      # Skip if too many mines or cells in either
      if left_bounds[2] > max_cells and left_bounds[0] > max_mines:
        continue

      if rights is None:
        rights = lefts

      added_exact = False

      for right in rights:
        if left == right or left & right == 0:
          continue

        right_bounds = ineqs.get(right)

        # Skip if too many mines or cells in either
        if right_bounds[2] > max_cells and right_bounds[0] > max_mines:
          continue

        if self.verbose:
          out2 = f'\n  right: {binary_to_cells(right)} : {right_bounds}'
          out3 = ''

        crossed = self.cross_ineqs(left, left_bounds, right, right_bounds)
        for new_ineq in crossed:
          ineq, added = self.add_ineq(new_ineq, ineqs, groups)
          any_added = any_added or added

          if added and ineq[0] == ineq[1]:
            added_exact = True

          if self.verbose and added:
            out3 += f'\n    crossed: {added}, {binary_to_cells(new_ineq[0]), new_ineq[1:]}'

        if self.verbose and out3:
          print(out2 + out3)

      if added_exact:
        break

    return any_added, eliminated

  def solve_fast(self):
    ineqs = dict()
    max_cells = 9
    max_mines = 3
    import time
    start_time = time.time()

    groups = {
      'trivial': set(),
      'fe_fe': set(),
      'fe_se': {'fresh': set(), 'stale': set()},
      'fe_fi': {'exact': set(), 'inexact': set()},
      'fe_si': {'fresh': set(), 'stale': set()},
      'fi_se': {'fresh': set(), 'stale': set()},
      'fi_fi': set(),
      'fi_si': {'fresh': set(), 'stale': set()},
    }

    for const in self.constraints:
      self.add_ineq(const, ineqs, groups)

    revealed = cells_to_binary(self.revealed)
    flagged = 0

    board_ineqs = dict()
    for tile_id, what, neighbors in self.board:
      if what == '.':
        cells = 0
        count = 0

        for neighbor in neighbors:
          cells += 2 ** neighbor
          if self.board[neighbor][1] == '*':
            count += 1

        if cells:
          board_ineqs[2 ** tile_id] = [cells, count, count, bin(cells).count('1')]

    for tile in self.revealed:
      ineq = board_ineqs.pop(2 ** tile, None)
      if ineq is not None:
        self.add_ineq(ineq, ineqs, groups)

    if self.verbose:
      print('starting ineqs:')
      for num, bounds in ineqs.items():
        print(f'  {binary_to_cells(num)} {bounds}')

    max_steps = -100
    finished = False

    while max_steps and not finished:
      max_steps -= 1
      finished = True

      # Stage: adjust
      to_add = []
      to_remove = []

      for num, bounds in ineqs.items():
        # if any cells were revealed or flagged, make a new inequality
        if num & (revealed | flagged):
          to_remove.append(num)

          new_num = num & ~revealed & ~flagged
          if not new_num:
            continue

          flagged_count = bin(num & flagged).count('1')
          new_count = bin(new_num).count('1')
          new_min = max([0, bounds[0] - flagged_count])
          new_max = min([new_count, max([0, bounds[1] - flagged_count])])

          to_add.append([new_num, new_min, new_max, new_count])

      for old_num in to_remove:
        self.pop_ineq(old_num, ineqs, groups)

      for new_ineq in to_add:
        _, added = self.add_ineq(new_ineq, ineqs, groups)
        finished = finished and not added

      if not ineqs:
        break

      if self.verbose:
        print('num ineqs:', len(ineqs))

      # Stage: use trivial
      if groups['trivial']:
        newly_revealed = 0
        newly_flagged = 0

        for num in groups['trivial']:
          bounds = ineqs.get(num)
          if self.verbose:
            print('trivial:', binary_to_cells(num), bounds)

          if not num & ~revealed & ~flagged:
            continue

          if bounds[1] == 0:  # revealed
            new_clear = num & ~revealed
            newly_revealed = newly_revealed | new_clear
            revealed = revealed | new_clear

            n = 1
            while n <= new_clear:
              if n & new_clear and n in board_ineqs:
                ineq, added = self.add_ineq(board_ineqs[n], ineqs, groups)

                if self.verbose:
                  print('added, n, board ineq:', added, n, binary_to_cells(board_ineqs[n][0]), ineq)

              n *= 2

          else:
            new_flag = num & ~flagged
            newly_flagged = newly_flagged | new_flag
            flagged = flagged | new_flag

        if self.verbose:
          print('newly_revealed:', binary_to_cells(newly_revealed))
          print('newly_flagged:', binary_to_cells(newly_flagged))

        groups['trivial'] = set()
        finished = False
        continue

      for name, value in groups.items():
        if name == 'trivial':
          continue

        if name == 'fe_fe' or name == 'fi_fi':
          lefts = value
          right_index = None

        elif name == 'fe_fi':
          lefts = value['exact']
          right_index = value['inexact']

        else:
          lefts = value['fresh']
          right_index = value['stale']

        if self.verbose:
          print('stage, num left, num right, time:', name, len(lefts), len(right_index) if right_index else len(lefts), '\t', time.time() - start_time)

        lefts_copy = lefts.copy()

        added, eliminated = self.cross_all_pairs(lefts_copy, right_index, ineqs, groups, max_cells=max_cells, max_mines=max_mines)

        lefts = lefts.difference(eliminated)
        if name == 'fe_fi':
          value['inexact'] = set()
        elif name not in ['fe_fe', 'fi_fi']:
          value['stale'].update(eliminated)

        finished = finished and not added
        if added:
          break

    print('revealed', binary_to_cells(revealed))
    print('flagged', binary_to_cells(flagged))

    return bool(ineqs)


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

  print(Puzzle(board, revealed, constraints, verbose=True).solve_fast())


def uncompress(width, height, compressed):
  board = []

  for i in range(width * height):
    neighbors = []
    board.append((i, compressed[i], neighbors))

    for dx in [-1, 0, 1]:
      if i % width + dx < 0 or i % width + dx >= width:
        continue

      for dy in [-1, 0, 1]:
        if i // width + dy < 0 or i // width + dy >= height:
          continue

        if [dx, dy] == [0, 0]:
          continue

        neighbors.append(i + dx + width * dy)

  constraints = [(compressed.count('*'), list(range(width * height)))]

  # vertical column hints
  for j in range(width):
    constraints.append((
      compressed[j::width].count('*'),
      [j + k * width for k in range(height)],
    ))

  # horizontal column hints
  for j in range(height):
    constraints.append((
      compressed[j * width:j * width + width].count('*'),
      list(range(j * width, j * width + width)),
    ))

  revealed = []

  return board, revealed, constraints


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

  board, revealed, constraints = uncompress(w, h, compressed)

  print('board:', board)
  print('constraints:')
  pprint.pprint(constraints, width=160)

  print(Puzzle(board, revealed, constraints, verbose=True).solve_fast())


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

  print(Puzzle(board, revealed, constraints, verbose=True).solve_fast())


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
