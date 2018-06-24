import sys
import random

from TametsiSolver import Puzzle, uncompress


def extract_difficulty_steps(puzzle):
  difficulty_steps = [0]
  step = 0

  for round in puzzle.rounds:
    if len(round['trivial'][-1]):
      difficulty_steps[step] += 1
      step = 0

    else:
      step += 1
      if step >= len(difficulty_steps):
        difficulty_steps.append(0)

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
  puzzle.solve()

  return extract_difficulty_steps(puzzle)


def raw_difficulty(width, height, compressed, multiplier=100):
  difficulty_steps = get_difficulty_steps(width, height, compressed)

  if difficulty_steps[-1] > 0:
    return sum([multiplier ** x * y for x, y in enumerate(difficulty_steps)])

  else:
    return 0


def smooth_difficulty(width, height, compressed):
  difficulty_steps = get_difficulty_steps(width, height, compressed)

  if difficulty_steps[-1] == 0:
    return 0

  if len(difficulty_steps) < 2:
    return difficulty_steps[0] ** 0.5

  score = 0

  for index in range(len(difficulty_steps) - 1):
    a, b = difficulty_steps[index:index + 2]
    x, y = min(a, b), max(a, b)

    score += x + x / (y - x + 1)

  return score


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
  choices = '..*'
  metric = smooth_difficulty

  for _ in range(seeds):
    compressed = ''.join([random.choice(choices) for x in range(width * height)])
    board_strings[compressed] = metric(width, height, compressed)

  best = list(board_strings.keys())[:]

  round_num = 0
  while 1:
    round_num += 1
    added = False

    for index, bstr1 in enumerate(best):
      for bstr2 in best[index:]:
        x = random.randint(1, width * height - 1)
        nstr = bstr1[:x] + bstr2[x:]

        # mutate
        for i in range(len(nstr)):
          if random.random() < 1 / 2:
            nstr = nstr[:i] + random.choice(choices) + nstr[i + 1:]

        if nstr not in board_strings:
          board_strings[nstr] = metric(width, height, nstr)
          added = True

    if not added:
      continue

    best = sorted(board_strings.keys(), key=lambda x: board_strings[x])[-seeds:]

    print("Best of round {}:".format(round_num))
    for bstr in best:
      print("String {} had score {}.".format(bstr, board_strings[bstr]))


if __name__ == '__main__':
  # CL_demo(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
  # random_demo(6, 6)
  evolutionary_demo(6, 6, int(sys.argv[1]) if len(sys.argv) > 1 else 10)
