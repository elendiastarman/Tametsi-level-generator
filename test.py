import sys
import time

from loader import load
from scorer import score


def run(level_id=None, verbose=False):
  names = []

  with open('test/index') as index:
    for line in index.read().split('\n'):
      id, name = line.split(' ')
      names.append(name)

      if level_id and id == level_id:
        names = [name]
        break

  print('names:', names)
  for index, name in enumerate(names):
    with open(f'test/{name}') as level:
      puzzle, reverse_id_map = load(level.read(), verbose=verbose)

    st = time.time()
    result = puzzle.solve()
    et = time.time()
    print(f'{index + 1} {name}: {et - st:.3f} seconds, solved {result["solved"]}')

    if verbose and not result['solved']:
      print('result:', result)
      flagged = ','.join([reverse_id_map[cell_id] for cell_id in result['flagged']])
      revealed = ','.join([reverse_id_map[cell_id] for cell_id in result['revealed']])
      print(f'P:_:{flagged}:{revealed}:n')

    continue
    scored = score(result)
    print(f'{index + 1} {name}: {et - st:.3f} seconds, score {scored}')


if __name__ == '__main__':
  if len(sys.argv) > 1:
    run(sys.argv[-1], verbose=('--verbose' in sys.argv))
  else:
    run()
