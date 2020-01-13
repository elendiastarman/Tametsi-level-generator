import sys
import random
import operator

from solver import Puzzle
from scorer import score
from templater import make_template


def score_candidate(board, revealed, constraints, compressed, score_method, verbose=False):
  board.sort(key=lambda x: x[0] in revealed)

  mapped = dict()
  for index, what in enumerate(compressed):
    board[index][1] = what
    mapped[board[index][0]] = what

  for constraint in constraints:
    constraint[0] = sum([mapped[i] == '*' for i in constraint[1]])

  puzzle = Puzzle(board, revealed, constraints, verbose=verbose, max_inexact_stages=1)
  result = puzzle.solve()
  return score(result, score_method), result


def random_compressed(num, probabilities):
  c = ''

  for index in range(num):
    r = random.random()
    if r <= probabilities[index][0]:
      c += '.'
    elif r <= probabilities[index][0] + probabilities[index][1]:
      c += '*'
    else:
      c += '?'

  return c


def iteration(template_method, score_method, *template_args, **template_kwargs):
  probabilities = [0.2, 0.5]  # First is for '.', second is for '*', and remainder is '?'
  num, board, revealed, constraints, sanity_check = make_template(template_method, *template_args, **template_kwargs)

  invert_sort = False  # True if lower scores are better
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
    prob_list = [probabilities] * num
    base = random_compressed(num, prob_list)

    while not sanity_check(base):
      base = random_compressed(num, prob_list)

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

    if len(scores) == 1 or comp(temp_threshold, 0.8 * threshold):
      probabilities[0] = (probabilities[0] + temp_best.count('.') / len(temp_best)) / 2
      probabilities[1] = (probabilities[1] + temp_best.count('*') / len(temp_best)) / 2

      output = 'Best of round {}: {} with score {}'.format(round_num, temp_best, temp_threshold)
      if comp(temp_threshold, limit):
        steps = ''.join(['T' if 'trivial' in step else 'E' if 'exact' in step else 'I' for step in temp_result['summary']])
        output += f' and steps {steps}'
      print(output)

    if comp(temp_threshold, threshold):
      probabilities[0] = temp_best.count('.') / len(temp_best)
      probabilities[1] = temp_best.count('*') / len(temp_best)
      threshold = temp_threshold
      print(' ^ Best so far!')


def gradient_ascent(template_method, score_method, *template_args, **template_kwargs):
  num, board, revealed, constraints, sanity_check = make_template(template_method, *template_args, **template_kwargs)
  starting_probabilities = [0.5, 0.25]  # First is for '.', second is for '*', and remainder is '?'

  trials = 100
  best_of = 10

  invert_sort = False  # True if lower scores are better
  if not invert_sort:
    limit = 0
    comp = operator.gt
  else:
    limit = float('inf')
    comp = operator.lt

  round_num = 0
  best_score = 0
  probabilities = [starting_probabilities[:] for _ in range(num)]

  while 1:
    solved = []
    round_num += 1

    while len(solved) < trials:
      candidate = random_compressed(num, probabilities)

      while not sanity_check(candidate):
        candidate = random_compressed(num, probabilities)

      scored, result = score_candidate(board, revealed, constraints, candidate, score_method)

      if comp(scored, limit):
        solved.append([scored, candidate, result])

    top = sorted(solved, key=lambda x: x[0], reverse=invert_sort)[-best_of:]

    if comp(top[-1][0], 0.8 * best_score):
      output = f'Best of round {round_num}: {top[-1][1]} with score {top[-1][0]}'
      if comp(scored, limit):
        output = output + ' and steps ' + ''.join(['T' if 'trivial' in step else 'E' if 'exact' in step else 'I' for step in top[-1][2]['summary']])
      print(output)

      score_total = sum([_[0] for _ in top])
      for index in range(num):
        probabilities[index][0] = sum([s * (c[index] == '.') for s, c, r in top]) / score_total
        probabilities[index][1] = sum([s * (c[index] == '*') for s, c, r in top]) / score_total

      # print('new probabilities:', '; '.join('{:.3f},{:.3f}'.format(*p) for p in probabilities))

    if comp(top[-1][0], best_score):
      best_score = top[-1][0]
      print(' ^ Best so far!')

    if sum([p in [[0, 0], [0, 1], [1, 0]] for p in probabilities]) > 0.8 * len(probabilities):
      print('\n<restarting>\n')
      best_score = 0
      probabilities = [starting_probabilities[:] for _ in range(num)]


if __name__ == '__main__':
  print('argv:', sys.argv)

  # iteration('combination_lock', 'seqnum', size)
  # gradient_ascent('combination_lock', 'seqnum', size)
  # gradient_ascent('cl_corner_bite', 'seqnum', size)
  # gradient_ascent('holey', 'seqnum', size)
  # gradient_ascent('l_shape_grid', 'seqnum', *sys.argv[1:])
  gradient_ascent(*sys.argv[1:])
