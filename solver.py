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

  def add_ineq(self, to_add, ineqs, indexes):
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

    if known[1] == 0 or known[0] == known[2]:
      indexes['trivial'].add(num)
      return known, True

    known_exact = known[0] == known[1]

    if old:
      old_exact = old[0] == old[1]
      if old_exact ^ known_exact:
        self.index_add_remove(indexes['exact' if old[0] == old[1] else 'inexact'], 'remove', num)

    self.index_add_remove(indexes['exact' if known_exact else 'inexact'], 'add', num)
    return known, True

  def pop_ineq(self, to_pop, ineqs, indexes):
    known = ineqs.pop(to_pop, None)

    if known:
      self.index_add_remove(indexes['stale'], 'remove', to_pop)
      self.index_add_remove(indexes['exact' if known[0] == known[1] else 'inexact'], 'remove', to_pop)

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

  def cross_all_pairs(self, left_index, right_index, ineqs, indexes, max_cells=9, max_mines=3):
    any_added = False
    num = 1
    seen = 0

    while num <= max(left_index):
      if num not in left_index or num not in right_index:
        seen = seen | num
        num *= 2
        continue

      lefts = left_index[num]
      rights = right_index[num].copy()

      for left in lefts:
        left_bounds = ineqs.get(left, None)
        if left_bounds is None or left_bounds[2] > max_cells and left_bounds[0] > max_mines:
          continue

        for right in rights:
          if left == right or left & seen and right & seen:
            continue

          right_bounds = ineqs.get(right, None)
          if right_bounds is None or right_bounds[2] > max_cells and right_bounds[0] > max_mines:
            continue

          crossed = self.cross_ineqs(left, left_bounds, right, right_bounds)
          for new_ineq in crossed:
            ineq, added = self.add_ineq(new_ineq, ineqs, indexes)
            any_added = added or any_added

      seen = seen | num
      num *= 2

    return any_added

  def solve_fast(self):
    ineqs = dict()
    max_cells = 9
    max_mines = 3

    indexes = {
      'trivial': set(),
      'exact': dict(),
      'inexact': dict(),
      'stale': dict(),
    }

    for const in self.constraints:
      self.add_ineq(const, ineqs, indexes)

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
        self.add_ineq(ineq, ineqs, indexes)

    if self.verbose:
      print('starting ineqs:')
      for num, bounds in ineqs.items():
        print(f'  {binary_to_cells(num)} {bounds}')

    # import ipdb; ipdb.set_trace()
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
        self.pop_ineq(old_num, ineqs, indexes)

      for new_ineq in to_add:
        _, added = self.add_ineq(new_ineq, ineqs, indexes)
        finished = finished and not added

      if not ineqs:
        break

      if self.verbose:
        print('num ineqs:', len(ineqs))

      # Stage: use trivial
      if indexes['trivial']:
        newly_revealed = 0
        newly_flagged = 0

        trivial = indexes['trivial']
        indexes['trivial'] = set()

        for num in trivial:
          if num not in ineqs:  # rare but okay
            continue

          bounds = ineqs[num]
          if self.verbose:
            print('trivial:', binary_to_cells(num), bounds)

          if not num & ~revealed & ~flagged:
            continue

          if bounds[1] == 0:  # revealed
            new_reveal = num & ~revealed
            newly_revealed = newly_revealed | new_reveal
            revealed = revealed | new_reveal

          else:
            new_flag = num & ~flagged
            newly_flagged = newly_flagged | new_flag
            flagged = flagged | new_flag

        if self.verbose:
          print('newly_revealed:', binary_to_cells(newly_revealed))
          print('newly_flagged:', binary_to_cells(newly_flagged))

        n = 1
        newly_changed = newly_revealed | newly_flagged
        while n <= newly_changed:
          if n & newly_changed:
            indexes['exact'].pop(n, None)
            indexes['inexact'].pop(n, None)
            indexes['stale'].pop(n, None)

          if n & newly_revealed and n in board_ineqs:
            ineq, added = self.add_ineq(board_ineqs[n], ineqs, indexes)

            if self.verbose:
              print('added, n, board ineq:', added, n, binary_to_cells(board_ineqs[n][0]), ineq)

          n *= 2

        finished = False
        continue

      if indexes['exact']:
        exact = indexes['exact']
        indexes['exact'] = dict()
        if self.verbose:
          print('num exact:', sum(map(len, exact.values())))

        added = self.cross_all_pairs(exact, exact, ineqs, indexes, max_cells, max_mines)
        added = self.cross_all_pairs(exact, indexes['inexact'], ineqs, indexes, max_cells, max_mines) or added
        added = self.cross_all_pairs(exact, indexes['stale'], ineqs, indexes, max_cells, max_mines) or added

        for bit, nums in exact.items():
          indexes['stale'].setdefault(bit, set()).update(nums)

        finished = finished and not added
        if added:
          continue

      if indexes['inexact']:
        inexact = indexes['inexact']
        indexes['inexact'] = dict()
        if self.verbose:
          print('num inexact:', sum(map(len, inexact.values())))

        added = self.cross_all_pairs(inexact, inexact, ineqs, indexes, max_cells, max_mines)
        added = self.cross_all_pairs(inexact, indexes['stale'], ineqs, indexes, max_cells, max_mines) or added

        for bit, nums in inexact.items():
          indexes['stale'].setdefault(bit, set()).update(nums)

        finished = finished and not added

    print('revealed', binary_to_cells(revealed))
    print('flagged', binary_to_cells(flagged))

    if ineqs:
      for num, bounds in ineqs.items():
        print('  ', binary_to_cells(num), bounds)

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

  print(Puzzle(board, revealed, constraints, verbose=False).solve_fast())


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
