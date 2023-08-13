import time
import random
import logging

from json import load
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from itertools import combinations, islice, tee

import numpy as np

from pydantic import BaseModel
from shapely.geometry import LineString

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def load_robots(dir="./data/json/"):
    paths = Path(dir).glob("*.json")
    return [
        robot
        for p in paths
        if p.is_file() and (robot := Robot.from_json(load(p.open())))
    ]


class Robot(BaseModel):
    device_id: str
    timestamp: float  # XXX: Um... I think?
    x: float
    y: float
    theta: float
    battery_level: float
    loaded: bool
    path: List[Dict[str, float]]
    paused: bool = False
    color: Optional[str] = None  # Who doesn't want to see colors?

    def __hash__(self):
        return hash(self.device_id)

    @classmethod
    def from_json(cls, json):
        return cls(**json)

    @property
    def is_idle(self):
        return not self.path

    def move(self):
        if self.is_idle:
            # logger.debug(f"Quick find some work {self.device_id} is idle!")
            return
        if self.paused:
            logger.debug(f"Robot {self.device_id} is paused")
            return

        next_step = self.path[0]
        dx = next_step["x"] - self.x
        dy = next_step["y"] - self.y

        # Figure out which direction to move in
        move_x = np.sign(dx)
        move_y = np.sign(dy)
        self.x += move_x
        self.y += move_y

        # XXX: Round down to the nearest integer, not sure if this could cause
        # problems, but float as coordinates is too much for my tiny brain.
        self.x = int(self.x)
        self.y = int(self.y)

        # Are we done with the path?
        if self.x == next_step["x"] and self.y == next_step["y"]:
            self.path.pop(0)
        self.timestamp = time.time()

        # logger.debug(f"Robot {self.device_id} @ ({self.x}, {self.y})")


class Grid:
    def __init__(self, robots, width, height):
        self.robots = robots
        self.width = width
        self.height = height
        self.grid = self.reset()
        self._update()

    def within_grid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def reset(self):
        # XXX: This should probably be a flat list instead of a 2D list but
        #      lets just get something working instead of being too smart
        return [[None for _ in range(self.width)] for _ in range(self.height)]

    def _update(self):
        self.grid = self.reset()
        for bot in self.robots:
            x, y = int(bot.x), int(bot.y)
            if not self.within_grid(x, y):
                logger.debug(
                    f"Houston we have a problem {bot.device_id} is out of bounds!"
                )
                bot.paused = True
                continue
            # XXX: For simulation just don't name robots with the same first
            #      letter and color
            self.grid[y][x] = (bot.device_id[0].upper(), bot.color)

    def render(self, to_disk=True):
        self._update()
        color_mapping = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": "\033[0m",
        }

        top_border = "-" * (2 * self.width + 1)
        bottom_border = top_border
        rendered_grid = [
            "|"
            + " ".join(
                color_mapping.get(cell[1], "") + cell[0] + color_mapping["reset"]
                if cell
                else " "
                for cell in row
            )
            + "|"
            for row in self.grid
        ]
        robot_info = "\n".join(
            f"{robot.device_id}: (x: {int(robot.x)}, y: {int(robot.y)})"
            for robot in self.robots
        )

        grid_state = "\n".join(
            [top_border] + rendered_grid + [bottom_border] + [robot_info]
        )

        # XXX: To visually monitor the robots, writing the grid to disk and using a tool
        #      like `inotifywait` to watch the file proved to be a much simpler way to
        #      iterate than trying to get the render in the event loop right. Optionally,
        #      it allows us to save the simulation as a series of text files if we want,
        #      which is kind of nice.
        if to_disk:
            with open(f"./data/output/screen.txt", "w") as f:
                f.write(grid_state)
            return

        # If we wanna print it
        return grid_state


def will_collide(current_bot: Robot, other_bot: Robot) -> bool:
    """Look ahead to see if the current bot will collide with other bot"""
    current_start = (current_bot.x, current_bot.y)
    current_end = (current_bot.path[0]["x"], current_bot.path[0]["y"])
    other_start = (other_bot.x, other_bot.y)
    other_end = (other_bot.path[0]["x"], other_bot.path[0]["y"])

    # XXX: Uses shapely to check if the lines intersect
    current_line = LineString([current_start, current_end])
    other_line = LineString([other_start, other_end])

    return current_line.intersects(other_line)


def collisions(robots: List[Robot]) -> List[Tuple[Robot, Robot]]:
    """Check if any robots are colliding and pause them if they are
    Returns a list of tuples of colliding robots
    """
    collisions_detected = []
    for current_bot, other_bot in combinations(robots, 2):
        if not (current_bot.is_idle or other_bot.is_idle):
            if will_collide(current_bot, other_bot):
                collisions_detected.append((current_bot, other_bot))
                current_bot.paused = True
                other_bot.paused = True
    return collisions_detected


def simulate(robots):
    """Lights camera action!"""
    grid = Grid(robots, 20, 20)
    while True:
        [robot.move() for robot in robots]
        grid.render()
        yield robots, grid


if __name__ == "__main__":
    # Simple path collision:
    # bots = load_robots(dir="./data/json/scenario_2/")
    # Task Example:
    bots = load_robots(dir="./data/json/scenario_1/")
    for robots, grid in simulate(bots):
        if colliding_bots := collisions(robots):
            print(
                f"Colliding robots detected: {', '.join(f'{bot1.device_id} & {bot2.device_id}' for bot1, bot2 in colliding_bots)}"
            )
            troblesome_bots = {bot for pair in colliding_bots for bot in pair}
            # XXX: Lets let the shortest path win, though we should probably
            #      just look at that path segment?
            sorted_troblesome_bots = sorted(
                list(troblesome_bots), key=lambda robot: len(robot.path)
            )
            for bot in sorted_troblesome_bots:
                print(f"Resuming robot {bot.device_id}")
                bot.paused = False
                while not bot.is_idle:
                    bot.move()
                    grid.render()
                    time.sleep(0.2)

        time.sleep(0.2)
