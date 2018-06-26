import sys
import random

from TametsiSolver import Puzzle, uncompress


def extract_difficulty_steps(puzzle):
  difficulty_steps = [0]

  for round in puzzle.rounds:
    difficulty_steps[-1] += 1

    if len(round['trivial'][-1]):
      difficulty_steps.append(0)

  if difficulty_steps[-1] == 0:
    difficulty_steps.pop()

  return difficulty_steps


def CL_demo(num):
  if num == 1:
    width, height = 6, 6
    compressed = '.*.?...*.?..*.***?**.?..*?*.*....*.?'

  elif num == 2:
    width, height = 6, 6
    compressed = '.***.*..*****.*..*.?.....*..*?.*.***'

  elif num == 6:
    width, height = 10, 10
    compressed = '**?....**.*...*.*......*......*.*.?**.*.**?.*??....**.?*.??.....*.***...........*?**.*...**.*?..**?.'

  board, revealed, constraints = uncompress(width, height, compressed)

  puzzle = Puzzle(board, revealed, constraints)
  solved = puzzle.solve()
  print("Solved?", solved)

  difficulty_steps = get_difficulty_steps(width, height, compressed)
  print("Score:", difficulty_steps)


def get_difficulty_steps(width, height, compressed):
  board, revealed, constraints = uncompress(width, height, compressed)
  puzzle = Puzzle(board, revealed, constraints)
  solved = puzzle.solve()

  return solved, extract_difficulty_steps(puzzle)


def raw_difficulty(width, height, compressed, multiplier=100):
  solved, difficulty_steps = get_difficulty_steps(width, height, compressed)

  if not solved:
    return -1

  return sum([multiplier ** x for x in difficulty_steps])


def smooth_difficulty(width, height, compressed):
  if not sanity_check(width, height, compressed):
    return -1

  solved, difficulty_steps = get_difficulty_steps(width, height, compressed)

  if not solved:
    return -1

  if len(difficulty_steps) < 2 or 0 in difficulty_steps:
    return -1

  score = 0

  for index in range(len(difficulty_steps) - 1):
    a, b = difficulty_steps[index:index + 2]
    x, y = min(a, b), max(a, b)

    score += x * (y - 1) / (y - x + 1)

  return score


def sanity_check(width, height, compressed):
  for w in range(width):
    if compressed[w::width].count('.') != height:
      return False

  for h in range(height):
    if compressed[h:h + width].count('.') != width:
      return False

  return True


def random_demo(width, height):
  max_score = 0

  while 1:
    compressed = ''.join([random.choice('..*') for x in range(width * height)])
    collapsed = raw_difficulty(width, height, compressed)

    if collapsed > max_score:
      max_score = collapsed
      print("Best so far: {} with collapsed score {}\n".format(compressed, collapsed))


def evolutionary_demo(width, height, seeds=10):
  board_strings = {}
  choices = '....**?'
  metric = smooth_difficulty

  for _ in range(seeds):
    compressed = ''.join([random.choice(choices) for x in range(width * height)])
    board_strings[compressed] = metric(width, height, compressed)

  best = list(board_strings.keys())[:]

  round_num = 0
  while 1:
    round_num += 1
    added_to_best = False

    while not added_to_best:
      bstr1 = random.choice(best)
      bstr2 = random.choice(best)
      if bstr1 == bstr2:
        continue

      x = random.randint(1, width * height - 1)
      nstr = bstr1[:x] + bstr2[x:]

      # mutate
      for i in range(len(nstr)):
        if random.random() < 1 / 2:
          nstr = nstr[:i] + random.choice(choices) + nstr[i + 1:]

      if nstr not in board_strings:
        board_strings[nstr] = metric(width, height, nstr)

        if board_strings[nstr] > board_strings[best[0]]:
          added_to_best = True

    best = sorted(board_strings.keys(), key=lambda x: board_strings[x])[-seeds:]

    print("Best of round {}:".format(round_num))
    for bstr in best:
      print("String {} had score {} (steps: {}).".format(bstr, board_strings[bstr], get_difficulty_steps(width, height, bstr)))


def iteration_demo(width, height):
  choices = '....**?'
  metric = smooth_difficulty
  max_score = 0
  round_num = 0

  while 1:
    round_num += 1
    base = ''.join([random.choice(choices) for x in range(width * height)])
    temp_max = metric(width, height, base)
    temp_best = base

    iteration = 0
    print("Round {}: ".format(round_num), end='', flush=True)

    while 1:
      print(iteration % 10, end='', flush=True)
      iteration += 1

      variants = {}

      for i in range(len(base)):
        for c in choices:
          if base[i] == c:
            continue

          v = base[:i] + c + base[i + 1:]

          if v not in variants:
            variants[v] = metric(width, height, v)
            print('.', end='', flush=True)

      best = sorted(variants.items(), key=lambda x: x[1])[-1]

      if best[1] > temp_max:
        base = best[0]
        temp_max = best[1]
        temp_best = base

      else:
        print()
        break

    print("Best of round {}: {} with score {} and steps {}".format(round_num, temp_best, temp_max, get_difficulty_steps(width, height, temp_best)))
    if temp_max > max_score:
      max_score = temp_max
      print(" ^ Best so far!")


if __name__ == '__main__':
  # CL_demo(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
  # random_demo(6, 6)
  # evolutionary_demo(6, 6, int(sys.argv[1]) if len(sys.argv) > 1 else 10)
  if len(sys.argv) > 2:
    w, h = map(int, sys.argv[1:3])
  else:
    w, h = 6, 6
  # iteration_demo(w, h)
  evolutionary_demo(w, h, int(sys.argv[3]) if len(sys.argv) > 3 else 10)
