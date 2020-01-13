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
  id_map = {board[index][0]: index for index in range(num)}
  starting_probabilities = [0.5, 0.25]  # First is for '.', second is for '*', and remainder is '?'

  trials = 50
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
      attempts = 10
      candidate = random_compressed(num, probabilities)

      while attempts:
        attempts -= 1

        scored, result = score_candidate(board, revealed, constraints, candidate, score_method)
        # print(f'score {scored} in {len(result["summary"])} rounds for candidate {candidate}')

        if comp(scored, limit):
          break

        result_known = result['revealed'].union(result['flagged'])
        boundary_empty = set()
        boundary_question = set()
        boundary_unknown = set()
        all_unknown = set()

        for cell_id, what, neighbors in board:
          if cell_id in result['revealed'] and set(neighbors).difference(result_known):
            if what == '.':
              boundary_empty.add(cell_id)
            elif what == '?':
              boundary_question.add(cell_id)
            else:
              raise ValueError('We got a problem here!')

          elif cell_id not in result_known:
            all_unknown.add(cell_id)

            if set(neighbors).intersection(result_known):
              boundary_unknown.add(cell_id)

        exploded = list(candidate)

        if boundary_question:
          for cell_id in boundary_question:
            exploded[id_map[cell_id]] = '.'

        elif boundary_unknown:
          replacements = list(random_compressed(len(boundary_unknown), probabilities))
          for cell_id in boundary_unknown:
            exploded[id_map[cell_id]] = replacements.pop()

        else:
          replacements = list(random_compressed(len(all_unknown), probabilities))
          for cell_id in all_unknown:
            exploded[id_map[cell_id]] = replacements.pop()

        candidate = ''.join(exploded)

        if sanity_check and not sanity_check(candidate):
          continue

        # import ipdb; ipdb.set_trace()

      solved.append([scored, candidate, result])

    top = sorted(solved, key=lambda x: x[0], reverse=invert_sort)[-best_of:]

    if comp(top[-1][0], 0.8 * best_score):
      # iteration stage - 1-char changes
      base_variant = top[-1]

      while 1:
        variants = []
        base_candidate = base_variant[1]

        for index in range(num):
          for char in ['.', '?', '*']:
            if char == base_candidate[index]:
              continue

            candidate = base_candidate[:index] + char + base_candidate[index + 1:]
            scored, result = score_candidate(board, revealed, constraints, candidate, score_method)
            variants.append([scored, candidate, result])

        best_variant = sorted(variants, key=lambda x: x[0], reverse=invert_sort)[-1]
        if not comp(best_variant[0], base_variant[0]):
          break
        base_variant = best_variant

      output = f'Best of round {round_num}: {base_variant[1]} with score {base_variant[0]}'
      if comp(base_variant[0], limit):
        output = output + ' and steps ' + ''.join(['T' if 'trivial' in step else 'E' if 'exact' in step else 'I' for step in base_variant[2]['summary']])
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
