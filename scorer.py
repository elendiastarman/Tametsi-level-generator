from math import log


def lognum(result):
  total_score = 0
  for step in result['summary']:
    if 'trivial' in step:
      total_score += 1
    elif 'exact' in step:
      total_score += log(step['exact']['count'])
    elif 'inexact' in step:
      total_score += log(step['inexact']['count'])

  return total_score


def seqnum(result):
  total_score = 0

  trivial_count = 0
  exact_count = 0
  exact_total = 0
  inexact_count = 0
  inexact_total = 0

  for step in result['summary']:
    if 'trivial' in step:
      trivial_count += 1
      # total_score += 1 / 2 ** trivial_count
      # total_score += 1 / trivial_count
      total_score += 1

    if 'exact' in step:
      exact_count += 1
      exact_total += step['exact']['count']
    elif exact_count:
      # total_score += 2 ** exact_count - 1
      # total_score += exact_total
      total_score += exact_count ** 2
      exact_count = 0
      exact_total = 0

    if 'inexact' in step:
      inexact_count += 1
      inexact_total += step['inexact']['count']
    elif inexact_count:
      # total_score += 2 / (2 ** inexact_count - 1)
      # total_score += inexact_total / inexact_count
      total_score += inexact_count ** 0.5
      inexact_count = 0
      inexact_total = 0

  return total_score


def score(result, method):
  if not result['solved']:
    return -1

  methods = dict(
    lognum=lognum,
    seqnum=seqnum,
  )

  return methods[method](result)
