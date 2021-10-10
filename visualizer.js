// little bit of setup

$$ = (selector => document.querySelector(selector))

let debug = $$('#debug')
let puzzle_data = $$('#puzzle-data')
let puzzle_soln = $$('#puzzle-soln')

puzzle_data.innerText = data.puzzle.replace('\\n', '\n')
puzzle_soln.innerText = JSON.stringify(data.solution, '', '  ')

// parse the puzzle

function extract(src, tag, regex, all) {
  let matcher = new RegExp(`<${tag}>${regex.source}</${tag}>`, regex.flags + 'g')
  let len = tag.length
  let match = src.match(matcher)
  if (match) {
    if (all)
      return match
    else
      return match[0].slice(len + 2, -(len + 3));
  }
  else
    return null;
}

function makePos(data) {
  return {x: parseFloat(data[0]), y: parseFloat(data[1])}
}

function makePoly(data) {
  let points = []
  for (let i = 0; i < data.length / 2; i += 1) {
    points.push(makePos(data.slice(2 * i, 2 * i + 2)))
  }
  return points
}

$$('#puzzle-id').innerText = extract(data.puzzle, 'ID', /\w+/)
$$('#puzzle-tile-text').innerText = extract(data.puzzle, 'TILE_TEXT', /\w+/)
$$('#puzzle-title').innerText = extract(data.puzzle, 'TITLE', /.+/)
$$('#puzzle-author').innerText = extract(data.puzzle, 'AUTHOR', /.+/)
let score = extract(data.puzzle, 'SCORE', /[\d\.]+/)
if (score)
  $$('#puzzle-score').innerText = ` (score = ${score})`

let nodes = {}
let nodeIds = []
let nodesSrc = extract(data.puzzle, 'NODE', /.+?/s, true)
nodesSrc.forEach(nodeSrc => {
  let nodeId = extract(nodeSrc, 'ID', /\d+/)
  let node = nodes[nodeId] = {}

  nodeIds.push(nodeId)
  node.id = nodeId
  node.src = nodeSrc
  node.edges = extract(nodeSrc, 'EDGES', /.+/).split(',')
  node.pos = makePos(extract(nodeSrc, 'POS', /.+/).split(','))
  node.poly = makePoly(extract(nodeSrc, 'POINTS', /.+/).split(','))
  node.has_mine = extract(nodeSrc, 'HAS_MINE', /.+/) == 'true'
  node.secret = extract(nodeSrc, 'SECRET', /.+/) == 'true'  // tiles with '?'
  node.revealed = extract(nodeSrc, 'REVEALED', /.+/) == 'true'  // tiles that start cleared
  node.flagged = false
  node.color = 'gray'
})

let hints = {column: [], color: []}
let columnHints = extract(data.puzzle, 'COLUMN_HINT', /.+?/s, true) || []
let colorHints = extract(data.puzzle, 'HINT', /.+?/s, true) || []

columnHints.forEach(hintSrc => {
  let hint = {type: 'column'}
  hint.ids = extract(hintSrc, 'IDS', /.+/).split(',')
  hint.location = makePos(extract(hintSrc, 'TEXT_LOCATION', /.+/).split(','))
  hint.rotation = parseFloat(extract(hintSrc, 'TEXT_ROTATION', /.+/))
  hint.size = parseFloat(extract(hintSrc, 'TEXT_SIZE_FACTOR', /.+/))
  hints.column.push(hint)
})

colorHints.forEach(hintSrc => {
  let hint = {type: 'color'}
  hint.ids = extract(hintSrc, 'IDS', /.+/).match(/\d+/g)
  hint.color = extract(hintSrc, 'COLOR', /.+/)
  hint.is_dark = extract(hintSrc, 'IS_DARK', /.+/) == 'true' ? 'dark' : ''
  hints.color.push(hint)

  hint.ids.forEach(nodeId => nodes[nodeId].color = hint.is_dark + hint.color)
})

// gray color hint
let grayHint = {type: 'color', ids: [], color: 'gray', is_dark: ''}
nodeIds.forEach(nodeId => {
  if (nodes[nodeId].color == 'gray')
    grayHint.ids.push(nodeId)
})
hints.color.unshift(grayHint)

let cornerFlag = extract(data.puzzle, 'CORNER_FLAG', /.+/) == 'true'

// now we start drawing things

function setRevealed(node, revealed) {
  if (node.revealed == revealed || node.flagged)
    return
  node.revealed = revealed

  if (node.revealed)
    $$(`#tile${node.id}`).setAttribute('fill', 'rgba(0, 0, 0, 0)')
  else
    $$(`#tile${node.id}`).setAttribute('fill', node.color)
}

function setFlagged(node, flagged) {
  if (node.flagged == flagged || node.revealed)
    return
  node.flagged = flagged

  if (node.flagged)
    $$(`#tile${node.id}`).setAttribute('fill', 'white')
  else
    $$(`#tile${node.id}`).setAttribute('fill', node.color)

  node.edges.forEach(neighborId => {
    let neighbor = nodes[neighborId]
    neighbor.flaggedCount += nodes[node.id].flagged ? 1 : -1
    if (!neighbor.has_mine && !neighbor.secret)
      $$(`#text${neighborId}`).innerHTML = neighbor.mineCount - neighbor.flaggedCount
  })

  // update column and color hints
  hints.column.forEach((hint, index) => {
    if (hint.ids.indexOf(node.id) == -1)
      return

    hint.flaggedCount += node.flagged ? 1 : -1
    $$(`#columnhint${index}`).innerHTML = hint.mineCount - hint.flaggedCount
  })
  hints.color.forEach((hint, index) => {
    if (hint.ids.indexOf(node.id) == -1)
      return

    hint.flaggedCount += node.flagged ? 1 : -1
    $$(`#colorhint${index}`).innerHTML = hint.mineCount - hint.flaggedCount
  })
}

function tileClick(event) {
  if (event.which == 2 || event.which == 3)
    event.preventDefault()

  let nodeId = event.target.id.slice(4)
  let node = nodes[nodeId]
  // console.log(event)
  if (event.which == 1) {
    // left click, reveals a tile
    setRevealed(node, true)
  } else if (event.which == 2) {
    // middle click, not used in-game but used here to clear state
    setRevealed(node, false)
    setFlagged(node, false)
  } else if (event.which == 3) {
    // right click, flags a tile
    setFlagged(node, !node.flagged)
  }
}

function tileHover(event) {
  let nodeId = event.target.id.slice(4)
  $$(`#overlay${nodeId}`).setAttribute('display', 'visible')
}

function tileLeave(event) {
  let nodeId = event.target.id.slice(4)
  $$(`#overlay${nodeId}`).setAttribute('display', 'none')
}

let maxX = maxY = 0
let minX = minY = minDist = Infinity
let tiles = $$('#svg-tiles')
nodeIds.forEach(nodeId => {
  let tile = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
  let node = nodes[nodeId]

  tile.setAttribute('id', `tile${nodeId}`)
  tile.setAttribute('x', node.pos.x)
  tile.setAttribute('y', node.pos.y)

  let tileMinX = tileMaxX = tileMinY = tileMaxY = 0
  let sumX = sumY = 0
  let pointstr = ''
  node.poly.forEach(point => {
    let px = point.x
    let py = point.y
    pointstr += `${px},${py} `

    tileMinX = Math.min(tileMinX, px)
    tileMaxX = Math.max(tileMaxX, px)
    tileMinY = Math.min(tileMinY, py)
    tileMaxY = Math.max(tileMaxY, py)
    sumX += px
    sumY += py
  })
  tile.setAttribute('points', pointstr)

  let centerX = (tileMinX + tileMaxX) / 2
  let centerY = (tileMinY + tileMaxY) / 2
  let minPointDist = (tileMaxX - tileMinX) + (tileMaxY - tileMinY)
  node.poly.forEach(point => {
    let px = point.x
    let py = point.y
    minPointDist = Math.min(minPointDist, ((px - centerX) ** 2 + (py - centerY) ** 2) ** 0.5)
  })
  minDist = Math.min(minDist, minPointDist)

  tile.setAttribute('fill', !node.revealed ? node.color : 'rgba(0, 0, 0, 0)')
  tile.setAttribute('stroke', 'lightgray')
  tile.setAttribute('stroke-width', '.25')

  let overlay = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
  overlay.setAttribute('id', `overlay${nodeId}`)
  overlay.setAttribute('points', pointstr)
  overlay.setAttribute('stroke', 'rgba(200, 200, 100, 0.5)')
  overlay.setAttribute('fill', 'rgba(200, 200, 100, 0.15)')
  overlay.setAttribute('pointer-events', 'none')
  overlay.setAttribute('display', 'none')

  let text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
  let char = ''
  if (node.has_mine)
    char = '*'
  else if (node.secret)
    char = '?'
  else {
    let mineCount = 0
    node.edges.forEach(nodeId => {
      if (nodes[nodeId].has_mine)
        mineCount += 1
    })
    if (mineCount)
      char = mineCount

    node.mineCount = mineCount
    node.flaggedCount = 0
  }
  text.innerHTML = char
  text.setAttribute('id', `text${nodeId}`)
  text.setAttribute('x', (tileMinX + tileMaxX) / 2)
  text.setAttribute('y', (tileMinY + tileMaxY) / 2 + 1)
  text.setAttribute('fill', char == '*' ? 'red' : 'lightgray')
  // text.setAttribute('font-size', `${(tileMaxY - tileMinY)}px`)
  text.setAttribute('dominant-baseline', 'middle')
  text.setAttribute('text-anchor', 'middle')

  let layers = document.createElementNS('http://www.w3.org/2000/svg', 'g')
  layers.append(text)
  layers.append(tile)
  layers.append(overlay)
  layers.setAttribute('transform', `translate(${node.pos.x},${node.pos.y})`)

  minX = Math.min(minX, node.pos.x + tileMinX)
  maxX = Math.max(maxX, node.pos.x + tileMaxX)
  minY = Math.min(minY, node.pos.y + tileMinY)
  maxY = Math.max(maxY, node.pos.y + tileMaxY)

  tile.addEventListener('mousedown', tileClick)
  tile.addEventListener('mouseenter', tileHover)
  tile.addEventListener('mouseleave', tileLeave)
  tile.addEventListener('contextmenu', e => e.preventDefault())

  tiles.append(layers)
})

// set font size
console.log('minDist', minDist)
nodeIds.forEach(nodeId => {
  $$(`#text${nodeId}`).setAttribute('font-size', `${minDist}px`)
})

// column hints
let columnGroup = $$('#svg-column-hints')
hints.column.forEach((hint, index) => {
  let text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
  let mineCount = 0
  hint.ids.forEach(nodeId => {
    if (nodes[nodeId].has_mine)
      mineCount += 1
  })
  hint.mineCount = mineCount
  hint.flaggedCount = 0

  text.innerHTML = mineCount
  text.setAttribute('id', `columnhint${index}`)
  text.setAttribute('x', hint.location.x)
  text.setAttribute('y', hint.location.y + 1)
  text.setAttribute('rotate', hint.rotation)
  text.setAttribute('fill', 'yellow')
  text.setAttribute('font-size', `${minDist * hint.size}px`)
  text.setAttribute('dominant-baseline', 'middle')
  text.setAttribute('text-anchor', 'middle')

  columnGroup.append(text)
})

// color hints
let colorGroup = $$('#svg-color-hints')
hints.color.forEach((hint, index) => {
  let text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
  let mineCount = 0
  hint.ids.forEach(nodeId => {
    if (nodes[nodeId].has_mine)
      mineCount += 1
  })
  hint.mineCount = mineCount
  hint.flaggedCount = 0
  
  text.innerHTML = mineCount
  text.setAttribute('id', `colorhint${index}`)
  text.setAttribute('x', minX - 3 * minDist)
  text.setAttribute('y', minY + index * (2 * minDist))
  text.setAttribute('fill', hint.is_dark + hint.color)
  text.setAttribute('font-size', `${minDist}px`)
  text.setAttribute('dominant-baseline', 'middle')
  text.setAttribute('text-anchor', 'middle')

  colorGroup.append(text)
})

let height = (maxY - minY) + 5 * minDist
let width = Math.max((maxX - minX) + 10 * minDist, height * 16 / 9)
console.log(`minX: ${minX}, maxX: ${maxX}`)
console.log(`minY: ${minY}, maxY: ${maxY}`)
console.log(`width: ${width}, height: ${height}`)
let svg = $$('#svg')
// svg.setAttribute('viewBox', `${minX - width / 10} ${minY - height / 10} ${width / 2} ${height * 3 / 4}`)
svg.setAttribute('viewBox', `${minX - 3 * minDist} ${minY - 2 * minDist} ${width} ${height}`)

// now for the solution stuff
let table = $$('#solution-steps')
let actionable = []  // trivial stages
data.solution.summary.push({num_ineqs: 0, done: true})

data.solution.summary.forEach((step, index) => {
  let row = document.createElement('tr')
  let round = document.createElement('td')
  let numIneqs = document.createElement('td')
  let stage = document.createElement('td')
  let revealed = document.createElement('td')
  let flagged = document.createElement('td')

  round.innerText = index
  numIneqs.innerText = step.num_ineqs

  if (step.exact)
    stage.innerText = `exact; ${step.exact.count}`
  else if (step.inexact)
    stage.innerText = `inexact; ${step.inexact.count}`
  else if (step.done) {
    stage.innerText = `(done)`
    actionable.push(index)
  }
  else if (step.trivial) {
    stage.innerText = `trivial`
    actionable.push(index)

    let spans = []
    step.trivial.revealed.forEach(nodeId => {
      let span = document.createElement('span')
      span.innerText = nodeId
      span.setAttribute('id', `span${nodeId}`)
      span.setAttribute('onmouseenter', 'tileHover(event)')
      span.setAttribute('onmouseleave', 'tileLeave(event)')
      // span.setAttribute('onclick', 'syncBoard(actionable.indexOf(parseInt(event.target.parentNode.parentNode.id.slice(5))))')
      spans.push(span.outerHTML)
    })
    revealed.innerHTML = spans.join(', ')
    
    spans = []
    step.trivial.flagged.forEach(nodeId => {
      let span = document.createElement('span')
      span.innerText = nodeId
      span.setAttribute('id', `span${nodeId}`)
      span.setAttribute('onmouseenter', 'tileHover(event)')
      span.setAttribute('onmouseleave', 'tileLeave(event)')
      // span.setAttribute('onclick', 'syncBoard(actionable.indexOf(parseInt(event.target.parentNode.parentNode.id.slice(5))))')
      spans.push(span.outerHTML)
    })
    flagged.innerHTML = spans.join(', ')
  }

  if (step.trivial || step.done)
    row.addEventListener('click', event => {
      let targetId
      if (event.target.tagName == 'TD')
        targetId = event.target.parentNode.id
      else if (event.target.tagName == 'SPAN')
        targetId = event.target.parentNode.parentNode.id
      syncBoard(actionable.indexOf(parseInt(targetId.slice(5))))
    })

  row.setAttribute('id', `round${index}`)
  row.append(round, numIneqs, stage, revealed, flagged)
  table.append(row)
})

// controls
let numRounds = actionable.length
let currentRow = 0

function syncBoard(newRow, force) {
  if (newRow < 0)
    newRow = 0
  if (newRow >= numRounds)
    newRow = numRounds - 1
  if (currentRow == newRow && !force)
    return

  $$(`#round${actionable[currentRow]}`).setAttribute('class', '')
  let index = actionable[currentRow]
  
  if (newRow > currentRow) {
    while (currentRow < newRow) {
      let trivial = data.solution.summary[index].trivial
      index += 1
      if (!trivial)
        continue

      trivial.revealed.forEach(nodeId => setRevealed(nodes[nodeId], true))
      trivial.flagged.forEach(nodeId => setFlagged(nodes[nodeId], true))
      currentRow += 1
    }
  }
  else if (newRow < currentRow) {
    while (currentRow > newRow) {
      index -= 1
      let trivial = data.solution.summary[index].trivial
      if (!trivial)
        continue

      trivial.revealed.forEach(nodeId => setRevealed(nodes[nodeId], false))
      trivial.flagged.forEach(nodeId => setFlagged(nodes[nodeId], false))
      currentRow -= 1
    }
  }

  currentRow = newRow
  $$(`#round${actionable[currentRow]}`).setAttribute('class', 'highlight')
}

function gotoStart() {
  syncBoard(0)
}
$$('#rewind').addEventListener('click', gotoStart)

function goBack() {
  syncBoard(currentRow - 1)
}
$$('#back').addEventListener('click', goBack)

function goForward() {
  syncBoard(currentRow + 1)
}
$$('#forward').addEventListener('click', goForward)

function gotoEnd() {
  syncBoard(numRounds - 1)
}
$$('#fast-forward').addEventListener('click', gotoEnd)

$$('#scroll').addEventListener('wheel', event => {
  console.log(event)
  event.preventDefault()
  if (event.deltaY < 0)
    goBack()
  else if (event.deltaY > 0)
    goForward()
})

syncBoard(0, true)
