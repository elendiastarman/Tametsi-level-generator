from solver import Puzzle
from scorer import score


def combination_lock(size):
  board = []
  revealed = []
  constraints = []

  for y in range(size):
    constraints.append([0, list(range(size * y, size * y + size))])  # horizontal
    constraints.append([0, list(range(y, size * size + y, size))])  # vertical

    for x in range(size):
      cell_id = x + size * y

      neighbors = []
      for dy in range(-1, 2):
        for dx in range(-1, 2):
          if dx == dy == 0:
            continue
          elif x + dx < 0 or x + dx >= size:
            continue
          elif y + dy < 0 or y + dy >= size:
            continue

          neighbors.append(x + dx + size * (y + dy))

      board.append([cell_id, '', neighbors])

  constraints.append([0, list(range(size ** 2))])

  def sanity_check(compressed):  # takes a compressed string
    h, v = [0] * size, [0] * size
    for i in range(size):
      for j in range(size):
        h[i] += compressed[i * size + j] == '*'
        v[i] += compressed[i + j * size] == '*'

    return 0 in h or 0 in v or size in h or size in v

  return size ** 2, board, revealed, constraints, sanity_check


def combination_lock_render(compressed, size):
  num, board, revealed, constraints, _ = combination_lock(size)

  tile_size = 10
  points = '-{s},-{s},{s},-{s},{s},{s},-{s},{s}'.format(s=0.96 * tile_size / 2)

  nodes = []
  columns = []

  for i in range(num):
    board[i][1] = compressed[i]
    nodes.append(dict(
      id=i,
      neighbors=board[i][2],
      position=((i % size) * tile_size, (i // size) * tile_size),
      has_mine=compressed[i] == '*',
      secret=compressed[i] == '?',
      points=points,
    ))

  for j in range(size):
    # horizontal column hints
    constraints[2 * j][0] = sum([compressed[i] == '*' for i in constraints[2 * j][1]])
    columns.append(dict(
      ids=constraints[2 * j][1],
      text_location=(-tile_size, j * tile_size),
    ))

    # vertical column hints
    constraints[2 * j + 1][0] = sum([compressed[i] == '*' for i in constraints[2 * j + 1][1]])
    columns.append(dict(
      ids=constraints[2 * j + 1][1],
      text_location=(j * tile_size, -tile_size),
    ))

  constraints[-1][0] = compressed.count('*')

  result = Puzzle(board, revealed, constraints).solve()
  scored = score(result, 'seqnum')
  title = f'Combination Lock {size}x{size} with score {scored}'
  tile_text = 'CLX'

  return title, tile_text, nodes, columns, scored


def make_template(method, *args, **kwargs):
  methods = dict(
    combination_lock=combination_lock,
  )

  return methods[method](*args, **kwargs)


def render_template(method, compressed, *args, **kwargs):
  methods = dict(
    combination_lock=combination_lock_render,
  )

  return methods[method](compressed, *args, **kwargs)
