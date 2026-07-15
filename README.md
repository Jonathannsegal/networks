# NBA Player Movements

> **Status:** Research/data exploration repository. This is a fork-derived analysis project and is not a hosted web application.

This is a script for visualization of NBA games from raw SportVU logs.

If you admire both Spurs' and Warriors' ball movement, Brad Stevens' playbook, or just miss KD in OKC you'll find this entertaining.

## Examples

![Spurs](https://github.com/linouk23/NBA-Player-Movements/blob/master/examples/spurs.gif)
![Warriors](https://github.com/linouk23/NBA-Player-Movements/blob/master/examples/warriors.gif)
![Celtics](https://github.com/linouk23/NBA-Player-Movements/blob/master/examples/celtics.gif)
![Durant](https://github.com/linouk23/NBA-Player-Movements/blob/master/examples/durant.gif)

## Usage

1. Clone this repo:

  ```bash
  $ git clone https://github.com/Jonathannsegal/networks.git
  $ cd networks
  ```

2. Choose any NBA game from ```data/2016.NBA.Raw.SportVU.Game.Logs``` directory.

3. Generate an animation for the play by running the following script:

  ```bash
  $ python3 main.py --path=Celtics@Lakers.json --event=140
  ```

  ```
  required arguments:
    --path PATH    a path to json file to read the events from

  optional arguments:
    --event EVENT  an index of the event to create the animation for
                   (indexing starts at zero; values beyond the available events
                   use the final event in the game)
    -h, --help     show the help message and exit
  ```

## Attribution

This repository retains the structure and example media of the original NBA Player Movements project while preserving Jonathan Segal's analysis work and datasets.
