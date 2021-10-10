import sys
import json
from loader import load


class CustomEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, set):
      return list(obj)

    # fallback for all other cases
    return json.JSONEncoder.default(self, obj)


if __name__ == '__main__':
  filename = sys.argv[1] if len(sys.argv) > 1 else 'latest.puz'

  # load and solve the puzzle
  with open(filename) as f:
    puzzle_contents = f.read()
    puzzle, _, _ = load(puzzle_contents)
  solution = puzzle.solve()

  # write out the solution
  with open(filename + '.soln', 'w') as f:
    solution_contents = json.dumps(solution, cls=CustomEncoder, indent=2)
    f.write(solution_contents)

  # put the data into a Javascript file so the webpage can read it
  with open('visualizer_data.js', 'w') as f:
    puzzle_contents = puzzle_contents.replace('\n', '\\n')  # JSON can't have real linebreaks
    f.write(f'''let data = {{
      "puzzle": "{puzzle_contents}",
      "solution": {solution_contents}
    }}''')

  # open the webpage
