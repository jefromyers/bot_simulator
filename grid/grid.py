import logging

# TODO: Update `Grid` so we can serialize it easier
# from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    
    # TODO: Must change the watcher scripts to allow a different path
    def render(self, fn=f"./data/output/screen.txt"):
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
        if fn:
            with open(fn, "w") as f:
                f.write(grid_state)

        return grid_state
