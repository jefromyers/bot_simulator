import time
import logging

from typing import Dict, List, Optional, Tuple

import numpy as np

from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

    def next_position(self) -> Tuple[int, int]:
        next_x = self.x + np.sign(self.path[0]["x"] - self.x)
        next_y = self.y + np.sign(self.path[0]["y"] - self.y)
        return int(next_x), int(next_y)

    def move(self):
        if self.is_idle:
            return
        if self.paused:
            logger.debug(f"Robot {self.device_id} is paused")
            return

        self.x, self.y = self.next_position() 

        next_step = self.path[0]

        # Are we done with the path?
        if self.x == next_step["x"] and self.y == next_step["y"]:
            self.path.pop(0)
        self.timestamp = time.time()

        # logger.debug(f"Robot {self.device_id} @ ({self.x}, {self.y})")
