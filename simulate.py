import time
import logging

from json import load
from typing import List, Tuple
from pathlib import Path
from itertools import combinations

from shapely.geometry import LineString

from grid.grid import Grid
from bots.simple import Robot

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def load_robots(dir="./data/json/"):
    paths = Path(dir).glob("*.json")
    return [
        robot
        for p in paths
        if p.is_file() and (robot := Robot.from_json(load(p.open())))
    ]

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


def path_distance(bot: Robot):
    if bot.path:
        start = (bot.x, bot.y)
        end = (bot.path[0]["x"], bot.path[0]["y"])
        return LineString([start, end]).length
    return 0

def can_resume(bot: Robot, all_bots: List[Robot]) -> bool:
    next_x, next_y = bot.next_position()
    
    for other_bot in all_bots:
        if other_bot == bot or other_bot.paused or other_bot.is_idle:
            continue

        # See if the next position of this bot collides with another moving bot
        if other_bot.x == next_x and other_bot.y == next_y:
            return False
            
    return True


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

            for bot1, bot2 in colliding_bots:
                bot1.paused = True
                bot2.paused = True

            for bot in bots:
                if bot.paused and can_resume(bot, bots):
                    logger.debug(f"Resuming robot {bot.device_id}")
                    bot.paused = False

        time.sleep(0.2)
