import sys
import time

from loader import load
from scorer import score


def run(level_id=None, verbose=False):
  filenames = []

  with open('test/index') as index:
    for line in index.read().split('\n'):
      id, name = line.split(' ')
      filenames.append(name)

      if level_id and id == level_id:
        filenames = [name]
        break

  print('filenames:', filenames)
  for index, filename in enumerate(filenames):
    with open(f'test/{filename}') as level:
      puzzle, name, reverse_id_map = load(level.read(), verbose=verbose)

    st = time.time()
    result = puzzle.solve()
    et = time.time()

    if verbose:
      print('result:', result)
      print('')
      for step in result['summary']:
        print(' ', step)

    if verbose and not result['solved']:
      flagged = ','.join([reverse_id_map[cell_id] for cell_id in result['flagged']])
      revealed = ','.join([reverse_id_map[cell_id] for cell_id in result['revealed']])
      print(f'P:_:{flagged}:{revealed}:n')

    scored = score(result, 'seqnum')
    print(f'{index + 1:3} {filename:20}: {et - st:.3f} seconds, solved {result["solved"]}, score {scored:.3f} - {name}')


if __name__ == '__main__':
  if len(sys.argv) > 1:
    run(sys.argv[-1], verbose=('--verbose' in sys.argv))
  else:
    run()
