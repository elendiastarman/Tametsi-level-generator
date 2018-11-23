import os
import sys
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from TametsiGenerator import smooth_difficulty

env = Environment(
  loader=FileSystemLoader('.'),
  autoescape=select_autoescape(['xml']),
)

level_template = env.get_template('leveltemplate.xml')


def write_level(width, height, compressed, **parameters):
  params = dict(
    title='test',
    tile_size=10,
  )
  params.update(parameters)

  tile_size = params['tile_size']
  points = '-{s},-{s},{s},-{s},{s},{s},-{s},{s}'.format(s=0.96 * tile_size / 2)

  nodes = []
  columns = []

  for i in range(width * height):
    neighbors = []
    nodes.append(dict(
      id=i,
      neighbors=neighbors,
      position=((i % width) * tile_size, (i // width) * tile_size),
      has_mine=compressed[i] == '*',
      secret=compressed[i] == '?',
      points=points,
    ))

    for dx in [-1, 0, 1]:
      if i % width + dx < 0 or i % width + dx >= width:
        continue

      for dy in [-1, 0, 1]:
        if i // width + dy < 0 or i // width + dy >= height:
          continue

        if [dx, dy] == [0, 0]:
          continue

        neighbors.append(i + dx + width * dy)

  # vertical column hints
  for j in range(width):
    columns.append(dict(
      ids=[j + k * width for k in range(height)],
      text_location=(j * tile_size, -tile_size),
    ))

  # horizontal column hints
  for j in range(height):
    columns.append(dict(
      ids=list(range(j * width, j * width + width)),
      text_location=(-tile_size, j * tile_size),
    ))

  params['nodes'] = nodes
  params['columns'] = columns
  params['puzzle_id'] = len(os.listdir('puzzles')) + 1

  level = level_template.render(**params)

  today = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d')
  filename_safe_title = params['title'].replace(' ', '-')

  name = 'puzzles/{}_{}.puz'.format(today, filename_safe_title)
  print("Filename:", name)

  with open(name, 'w') as file:
    file.write(level)


if __name__ == '__main__':
  if len(sys.argv) < 4:
    width, height = 6, 6
    compressed = '.*.?...*.?..*.***?**.?..*?*.*....*.?'  # CL 1
  else:
    width = int(sys.argv[1])
    height = int(sys.argv[2])
    compressed = sys.argv[3]

  # title = 'test_' + compressed.replace('.', '0').replace('*', '1').replace('?', '2')
  # tile_text = 'EXP'

  score = round(smooth_difficulty(width, height, compressed), 2)
  title = 'Combination Lock {}x{} with score {}'.format(width, height, score)
  tile_text = 'CLX'

  write_level(width, height, compressed, title=title, score=score, tile_text=tile_text)
