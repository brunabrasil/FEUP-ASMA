from spade.agent import Agent
from spade.behaviour import CyclicBehaviour


class Drone(Agent):
    def __init__(self, jid, password, capacity, autonomy, velocity):
        super().__init__(jid, password)
        self.capacity = capacity
        self.autonomy = autonomy
        self.velocity = velocity
        self.battery_level = 100  # Initial battery level
        self.current_location = None
        self.destination = None

    async def setup(self):
        print(f"Drone {self.jid} is ready")




