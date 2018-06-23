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


if __name__ == '__main__':
  # width, height = 6, 6
  width, height = 10, 10
  # compressed = '.*.?...*.?..*.***?**.?..*?*.*....*.?'
  # compressed = '.***.*..*****.*..*.?.....*..*?.*.***'
  compressed = '**?....**.*...*.*......*......*.*.?**.*.**?.*??....**.?*.??.....*.***...........*?**.*...**.*?..**?.'
  board, revealed, constraints = uncompress(width, height, compressed)

  puzzle = Puzzle(board, revealed, constraints)
  puzzle.solve()

  score = score_puzzle(puzzle)
  print("Score:", score)
