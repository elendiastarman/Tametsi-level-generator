import sys
import time
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from templater import render_template

env = Environment(
  loader=FileSystemLoader('.'),
  autoescape=select_autoescape(['xml']),
)

level_template = env.get_template('leveltemplate.xml')


def write_level(board_template, compressed, *template_args, **parameters):
  params = dict(
    title='test',
    tile_size=10,
  )
  params.update(parameters)

  title, tile_text, nodes, columns, score = render_template(board_template, compressed, *template_args)

  params['nodes'] = nodes
  params['columns'] = columns
  params['puzzle_id'] = int(time.time())
  params['title'] = title
  params['tile_text'] = tile_text
  params['score'] = score

  level = level_template.render(**params)

  today = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d')
  filename_safe_title = params['title'].replace(' ', '-')

  name = f'puzzles/{today}_{filename_safe_title}.puz'
  print("Filename:", name)

  with open(name, 'w') as file:
    file.write(level)


if __name__ == '__main__':
  print('argv:', sys.argv)
  if len(sys.argv) > 2:
    compressed = sys.argv[1]
    size = int(sys.argv[2])
  else:
    compressed = '.*.?...*.?..*.***?**.?..*?*.*....*.?'  # CL 1
    size = 6

  write_level('combination_lock', compressed, size)
