import re
import sys
import time
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from templater import render_template

# Jinja2 setup stuff
env = Environment(
  loader=FileSystemLoader('.'),
  autoescape=select_autoescape(['xml']),
)

level_template = env.get_template('leveltemplate.xml')
# ^^^ this is a jinja2 renderer that loads a file and later, when .render is called, fills out the file with the given variables
# this is a generic file that captures the overall structure of a Tametsi puzzle file


def write_level(board_template, compressed, *template_args, **parameters):
  # default but overwritable attributes
  params = dict(
    tile_size=10,
  )
  params.update(parameters)

  # render_template takes a template (actually the lookup name) that then gets instantiated
  # according to the compressed string (and any extra args like size) and returns its attributes
  # this does solve the ensuing puzzle in order to give its score
  params = render_template(board_template, compressed, *template_args)
  params['puzzle_id'] = int(time.time())  # there's probably a better way to do this but ids need to be unique, otherwise Tametsi gets confused

  # params['nodes'] = describes the cells and their relations with each other
  # params['columns'] = groups some cells into some number of column hints (in any direction, including horizontal and diagonal) [technically *any* set of cells]
  # params['colors'] = groups some cells into some number of color hints
  # params['title'] = this is displayed in-game while solving the puzzle
  # params['tile_text'] = this is displayed in-game while choosing a puzzle
  # params['score'] = the computed score of the puzzle

  # Jinja-render the template file with this info
  level = level_template.render(**params)

  # vvv This just makes a unique filename
  today = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d')
  filename_safe_title = params['title'].replace(' ', '-')

  name = f'puzzles/{today}_{filename_safe_title}.puz'
  print(name)
  # ^^^

  # Write to the filename and also the latest file, for immediate testing
  with open(name, 'w') as file:
    file.write(level)

  with open('latest.puz', 'w') as file:
    file.write(level)


# python writer.py <template_name> <compressed> [arg1] [arg2] ...
# <compressed> is a string of `.*?` that represent the cells as empty (.), mined (*), or unknown (?)

if __name__ == '__main__':
  # write_level('combination_lock', compressed, size)
  # write_level('cl_corner_bite', compressed, size)
  # write_level('holey', compressed, size)
  # write_level('l_shape_grid', compressed, size, depth)
  args = [int(arg) if re.match(r'\d+', arg) else arg for arg in sys.argv[1:]]

  write_level(*args)  # just pipes in the command line args
