import re
from solver import Puzzle


def load(contents, verbose=False):
  id_map = dict()
  nodes = []
  total_mines = 0
  initial_revealed = []

  # Not parsing arbitrary XML here!
  matches = re.finditer('<NODE>.*?</NODE>', contents, re.DOTALL)
  for match in matches:
    node = match.group(0)

    node_id = re.search('<ID>(.*?)</ID>', node).group(1)
    neighbor_ids = re.search('<EDGES>(.*?)</EDGES>', node).group(1).split(',')
    revealed = bool(re.search('<REVEALED>[Tt]rue</REVEALED>', node))
    has_mine = bool(re.search('<HAS_MINE>[Tt]rue</HAS_MINE>', node))
    secret = bool(re.search('<SECRET>[Tt]rue</SECRET>', node))

    if neighbor_ids == ['']:  # no neighbors
      neighbor_ids = []
    if revealed:
      initial_revealed.append(node_id)
    if has_mine:
      total_mines += 1

    node_info = dict(
      node_id=node_id,
      neighbor_ids=neighbor_ids,
      revealed=revealed,
      has_mine=has_mine,
      secret=secret,
    )
    id_map[node_id] = len(nodes)
    nodes.append(node_info)

  # Hack for 94: Gridlock III (that the dev had to do too)
  if re.search('<ID>(.*?)</ID>', contents).group(1) == '2256502332117638':
    initial_revealed = '0,96,33,66,3,35,99,36,37,69,6,39,9,46,26,90,60,93,30,63'.split(',')

  board = []
  revealed = [id_map[revealed_id] for revealed_id in initial_revealed]
  constraints = []

  for node in nodes:
    cell = [
      id_map[node['node_id']],
      '*' if node['has_mine'] else '?' if node['secret'] else '.',
      [id_map[neighbor_id] for neighbor_id in node['neighbor_ids']],
    ]
    board.append(cell)

  constraints.append([total_mines, list(range(len(nodes)))])
  gray_mines = [total_mines, set(range(len(nodes)))]

  hints = re.finditer('<(COLUMN_)?HINT>.*?</(COLUMN_)?HINT>', contents, re.DOTALL)
  for hint in hints:
    mapped_ids = []
    mine_count = 0

    ids = re.search('<IDS>(.*?)</IDS>', hint.group(0)).group(1).split(',')
    for hint_id in ids:
      hint_id = id_map[hint_id]
      mapped_ids.append(hint_id)
      mine_count += nodes[hint_id]['has_mine']

    constraints.append([mine_count, mapped_ids])

    if 'COLUMN' not in hint.group(0):
      gray_mines[0] -= mine_count
      gray_mines[1].difference_update(set(mapped_ids))

  if total_mines != gray_mines[0]:
    gray_mines[1] = sorted(gray_mines[1])
    constraints.append(gray_mines)

  if verbose:
    print('board:')
    for cell in board:
      print(' ', cell)
    print('revealed:', revealed)
    print('constraints:')
    for constraint in constraints:
      print(' ', constraint)

  name = re.search('<TITLE>(.+?)</TITLE>', contents).group(1)
  reverse_id_map = [node['node_id'] for node in nodes]
  return Puzzle(board, revealed, constraints, verbose=verbose), name, reverse_id_map


def substitute(contents, verbose=False):
  """Takes a puzzle file and pulls nodes, column hints,
  and color hints out of it with new data substituted in"""
  nodes = []

  # Not parsing arbitrary XML here!
  matches = re.finditer('<NODE>.*?</NODE>', contents, re.DOTALL)
  for match in matches:
    node = match.group(0)

    node_id = re.search('<ID>(.*?)</ID>', node).group(1)
    neighbor_ids = re.search('<EDGES>(.*?)</EDGES>', node).group(1).split(',')
    position = re.search('<POS>(.*?)</POS>', node).group(1).split(',')
    points = re.search('<POINTS>(.*?)</POINTS>', node).group(1)
    revealed = bool(re.search('<REVEALED>[Tt]rue</REVEALED>', node))
    has_mine = bool(re.search('<HAS_MINE>[Tt]rue</HAS_MINE>', node))
    secret = bool(re.search('<SECRET>[Tt]rue</SECRET>', node))

    if neighbor_ids == ['']:  # no neighbors
      neighbor_ids = []

    nodes.append(dict(
      id=node_id,
      neighbors=neighbor_ids,
      position=position,
      points=points,
      revealed=revealed,
      has_mine=has_mine,
      secret=secret,
    ))

  columns = []
  colors = []
  hints = re.finditer('<(COLUMN_)?HINT>.*?</(COLUMN_)?HINT>', contents, re.DOTALL)
  for hint in hints:
    hint_src = hint.group(0)
    ids = re.search('<IDS>(.*?)</IDS>', hint_src).group(1).split(',')

    if 'COLUMN' not in hint.group(0):  # that is, a color hint
      colors.append(dict(
        ids=ids,
        color=re.search('<COLOR>(.*?)</COLOR>', hint_src).group(1),
        is_dark=re.search('<IS_DARK>(.*?)</IS_DARK>', hint_src).group(1),
      ))
    else:
      columns.append(dict(
        ids=ids,
        text_location=re.search('<TEXT_LOCATION>(.*?)</TEXT_LOCATION>', hint_src).group(1).split(','),
        text_rotation=re.search('<TEXT_ROTATION>(.*?)</TEXT_ROTATION>', hint_src).group(1),
        text_size_factor=re.search('<TEXT_SIZE_FACTOR>(.*?)</TEXT_SIZE_FACTOR>', hint_src).group(1),
      ))

  name = re.search('<TITLE>(.+?)</TITLE>', contents).group(1)
  reverse_id_map = [node['id'] for node in nodes]
  return dict(
    name=name,
    reverse_id_map=reverse_id_map,
    nodes=nodes,
    columns=columns,
    colors=colors,
  )
