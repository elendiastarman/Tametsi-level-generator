import sys

from TametsiSolver import Puzzle, uncompress


def score_puzzle(puzzle):
  difficulty = 0
  difficulty_step = 1
  multiplier = 100

  for round in puzzle.rounds:
    if len(round['trivial'][-1]):
      difficulty += difficulty_step
      difficulty_step = 1

    else:
      difficulty_step *= multiplier

  return difficulty


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

  score = score_puzzle(puzzle)
  print("Score:", score)


if __name__ == '__main__':
  CL_demo(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
