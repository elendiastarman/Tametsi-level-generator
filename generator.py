import sys
import random
import operator

from solver import Puzzle
from scorer import score
from templater import make_template


def score_candidate(board, revealed, constraints, compressed, score_method):
  for index, what in enumerate(compressed):
    board[index][1] = what

  for constraint in constraints:
    constraint[0] = sum([board[i][1] == '*' for i in constraint[1]])

  constraints.append([compressed.count('*'), list(range(len(compressed)))])

  puzzle = Puzzle(board, revealed, constraints, max_inexact_stages=1)
  result = puzzle.solve()
  return score(result, score_method), result


def iteration(template_method, score_method, *template_args, **template_kwargs):
  choices = '......***?'
  num, board, revealed, constraints, sanity_check = make_template(template_method, *template_args, **template_kwargs)

  invert_sort = False
  if invert_sort:
    limit = float('inf')
    comp = operator.lt
  else:
    limit = 0
    comp = operator.gt

  threshold = limit
  round_num = 0
  scores = []

  while 1:
    base = ''.join([random.choice(choices) for x in range(num)])

    while not sanity_check(base):
      base = ''.join([random.choice(choices) for x in range(num)])

    round_num += 1
    temp_threshold = score_candidate(board, revealed, constraints, base, score_method)[0]
    temp_best = base
    temp_result = None

    iteration = 0
    while 1:
      iteration += 1

      variants = {}

      for i in range(len(base)):
        for c in '.*?':
          if base[i] == c:
            continue

          v = base[:i] + c + base[i + 1:]

          if v not in variants and sanity_check(v):
            variants[v] = score_candidate(board, revealed, constraints, v, score_method)

      best = sorted(variants.items(), key=lambda x: x[1][0], reverse=invert_sort)[-1]

      if comp(best[1][0], temp_threshold):
        temp_best = best[0]
        temp_threshold = best[1][0]
        temp_result = best[1][1]

      else:
        break

    scores.append(temp_threshold)

    if comp(temp_threshold, sum(scores) / len(scores)):
      output = 'Best of round {}: {} with score {}'.format(round_num, temp_best, temp_threshold)
      if comp(temp_threshold, limit):
        steps = ''.join(['T' if 'trivial' in step else 'E' if 'exact' in step else 'I' for step in temp_result['summary']])
        output += f' and steps {steps}'
      print(output)

    if comp(temp_threshold, threshold):
      threshold = temp_threshold
      print(' ^ Best so far!')


if __name__ == '__main__':
  print('argv:', sys.argv)
  if len(sys.argv) > 1:
    size = int(sys.argv[1])
  else:
    size = 6

  iteration('combination_lock', 'seqnum', size)
