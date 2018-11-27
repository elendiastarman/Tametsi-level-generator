The example values below generally come from the puzzle file for **TMI: Green** (filename: `2018_01_29_A.puz`) with a few exceptions.

    <PUZZLE>

Starts the puzzle definition. Any tag other than those that follow is ignored (which can be used to e.g. put author attribution in the meta section).

      <ID>X500TMI1</ID>

Must be alphanumeric (`A-Z`, `a-z`, and `0-9` only) and is assumed to be unique. Tametsi won't crash if there are duplicate ids but only one of them will be displayed (and puzzle progress is also tracked on a per-id basis). Also, puzzles are presented in alphabetical order, so if you want your puzzles to show up after the 60 bonus puzzles included with the game, which all have ids that start with `X`, pick something like `Y`.

      <META>

Starts the info section of the puzzle.

        <TILE_TEXT>TMI</TILE_TEXT>

The text that appears on the tile at the level select screen. Recommended number of characters is at most 3, which fits comfortably within the tile size on the level select screen.

        <NEXT_PUZZLE_ID>X500TMI2</NEXT_PUZZLE_ID>

If this is specified, then after completing a puzzle, an arrow will appear at the right hand side which loads the next puzzle when clicked.

        <UNLOCKED_BY_AMOUNT>false</UNLOCKED_BY_AMOUNT>

A boolean that specifies whether a given number of puzzles need to be unlocked (not necessarily solved) first.

        <REQUIRE_ALL_UNLOCK_PUZZLES>true</REQUIRE_ALL_UNLOCK_PUZZLES>

A boolean that specifies whether all of the 100 main puzzles need to be unlocked (not necessarily solved).

        <REQUIRE_PERFECT>false</REQUIRE_PERFECT>

A boolean that specifies whether all 100 main puzzles need to be solved perfectly before this one is unlocked.

        <UNLOCK_PUZZLES>45</UNLOCK_PUZZLES>

A list of puzzle IDs that specifies which puzzles must be unlocked before this one is unlocked. If empty, then this doesn't apply.

        <UNLOCK_AMOUNT>0</UNLOCK_AMOUNT>

An integer that specifies the number of puzzles that must be unlocked before this one is unlocked.

      </META>

      <TITLE>TMI: Green</TITLE>

The title of the puzzle that runs up the left side of the window.

      <GRAPH>

Encapsulates the definition of the tiles themselves. "Graph" here is used in a mathematical sense where it is a collection of vertices (called "nodes" here) and edges. The nodes are the tiles themselves and the edges denote neighboring tiles.

        <NODE>

Starts the specification of a single node.

          <ID>7</ID>

An integer uniquely identifying this tile.

          <EDGES>21,22,8</EDGES>

A comma-separated list of tile ids. Ids used here must be defined somewhere in this file.

          <POS>304.5418453393238,360.0</POS>

A comma-separated pair of floats for `x,y` coordinates. **Note: Tametsi autoscales the entire puzzle, so all coordinates should be considered to be relative.**

          <POLY>

Specifies the specific polygonal shape of this tile.

            <POINTS>22.76323192340303,13.142358078602618,22.76323192340303,-13.142358078602618,-1.0063284153965543E-14,-26.28471615720524,-22.76323192340303,-13.142358078602612,-22.76323192340303,13.142358078602618,1.6094746754209057E-15,26.28471615720524</POINTS>

A comma-separated list of coordinate pairs for the vertices of the polygon. For example, a square would have a coordinate list looking like `x0,y0,x1,y1,x2,y2,x3,y3`. Tametsi draws edges in the order given, from `x0,y0` to `x1,y1`, then from there to `x2,y2` and so on.

            <HIGHLIGHTS>0,1,2,3</HIGHLIGHTS>

A comma-separated list of integers denoting the vertices included in the highlight. Highlights roughly simulate the effect of a light source and work on the *edges* between the specified vertices. Tametsi assumes that the specified vertices are consecutive, though they may wrap around as desired (e.g. `5,6,0,1` is valid).

            <HIGHLIGHTS_TAPER_START>true</HIGHLIGHTS_TAPER_START>

A boolean that specifies whether the first highlighted edge has a gradient in brightness from 0 at the first vertex to 1 at the second.

            <HIGHLIGHTS_TAPER_END>true</HIGHLIGHTS_TAPER_END>

A boolean that specifies whether the last highlighted edge has a gradient in brightness from 1 at the first vertex to 0 at the second.

          </POLY>

          <X_SCALING>0.5</X_SCALING>
          <Y_SCALING>0.5</Y_SCALING>

Floats that specify how much to scale border-related graphical elements of this tile. Useful when this tile is larger than others around it so the borders, which would otherwise be proportionally larger, don't look too funky.

          <REVEALED>true</REVEALED>

A boolean that specifies whether this tile is revealed at the start of the level.

          <HAS_MINE>true</HAS_MINE>

A boolean that specifies whether this tile has a mine under it.

          <SECRET>true</SECRET>

A boolean that specifies whether this tile displays a question mark for the hint when it is revealed.

        </NODE>

      </GRAPH>

      <HINT_LIST>

These are for the color-based hints that show up in the upper right corner of the window.

        <HINT>

Specifies the attributes of a given color hint.

          <IDS>96,128,97,98,99,140,141,110,142,111,112,113,82,114,83,84,125,126,127</IDS>

A comma-separated list of tile ids included in this color. Tametsi will draw them in the specified color.

          <COLOR>GREEN</COLOR>

A string that specifies the color of the tiles in this group. Must be one of `RED, ORANGE, YELLOW, GREEN, BLUE, INDIGO, VIOLET, PINK, GREY`. The `GREY` option is only useful when combined with the following `IS_DARK` option. Check this for a general color palette: https://i.stack.imgur.com/ngeGq.png

          <IS_DARK>false</IS_DARK>

A boolean that specifies whether the given color should be darkened. If the chosen color is `GREY` and this is `true`, then Tametsi draws it as black.

        </HINT>

      </HINT_LIST>

      <COLUMN_HINT_LIST>

Column hints simply indicate the number of mines within a group of mines. Typically, this is a row or column, but can also be diagonal or even bent in the middle.

        <COLUMN_HINT>

Specifies the attributes of a given column hint.

          <IDS>210,195,180,165,150,135,120,105</IDS>

A comma-separated list of ids of the tiles included in the column hint.

          <TEXT_LOCATION>431.5367181751513,69.48471615720524</TEXT_LOCATION>

A comma-separated pair of float for `x,y` coordinates of the column hint.

          <TEXT_ROTATION>0.0</TEXT_ROTATION>

A float that specifies the number of degrees clockwise to rotate the column hint.

          <TEXT_SIZE_FACTOR>1.0</TEXT_SIZE_FACTOR>

A float that specifies the scale of the column hint (e.g., 2.0 would mean it was twice as large).

          <BENT>true</BENT>

A boolean that specifies whether a column hint's line should be bent due to the included tiles changing direction, as with the `BOX` bonus puzzles.

        </COLUMN_HINT>

      </COLUMN_HINT_LIST>

      <TEXT>Hello world!</TEXT>

If not empty, then this text will display at the bottom of the window.

      <TEXT_POS>0.0,0.0</TEXT_POS>

The position of the bottom text. Be warned that this may not be well-supported for bonus puzzles (the only puzzles that have text like this are the first ten, the tutorial puzzles).

      <CORNER_FLAG>false</CORNER_FLAG>

A boolean that specifies whether the yellow "has corners" icon should be present in the upper right corner. Tametsi makes no effort to validate this so it is your responsibility to get it right.

    </PUZZLE>