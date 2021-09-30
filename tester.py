import sys
import time

from loader import load
from scorer import score


def run(level_id=None, verbose=False):
  # a shorthand to make it easy to test the latest puzzle you generated
  if level_id == '-1':
    filenames = ['../latest.puz']

  else:
    filenames = []
    # if you've just cloned the repo, this test/index file does not exist!
    # this file solely consists of lines in the form "[id] [filename]"
    # where filenames are in that same folder
    with open('test/index') as index:
      for line in index.read().split('\n'):
        id, name = line.strip().split(' ')
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


# python test.py [puzzle_id [--verbose]]
# with no args, this runs the scorer on all puzzles defined in /test/index
# with a puzzle id, this runs the scorer on that one (defined in /test/index)
# --verbose enables a ton of debug print statements

# NOTE THAT YOU NEED TO CREATE /test and put puzzle files in there
# AS WELL AS /test/index
# which is formatted like:
#   puzzle_id puzzle_filename

if __name__ == '__main__':
  if len(sys.argv) > 1:
    run(sys.argv[-1], verbose=('--verbose' in sys.argv))
  else:
    run()
