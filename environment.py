import pandas as pd
import spade
from drone import Drone
from center import Center
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

drones = []
centers = []

class Environment(Agent):

    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.drones = []


    async def initiate(self):
        df_center1 = pd.read_csv("data/delivery_center1.csv", delimiter=";")
        df_center2 = pd.read_csv("data/delivery_center2.csv", delimiter=";")
        df_drones = pd.read_csv("data/delivery_drones.csv", delimiter=";")

        print(len(df_drones))
        for index, row in df_drones.iterrows():    
            # Create an instance of the Drone class using the extracted information
            drone = Drone(row['id'] + "@localhost", "password", row['capacity'], row['autonomy'], row['velocity'], row['initialPos'], 2)
            await drone.start()
            drones.append(drone)
        
        center1 = Center("center1@localhost", "password", df_center1, drones)
        await center1.start()

        # center2 = Center("center2@localhost", "password", df_center2, drones)
        # await center2.start()

    
    async def setup(self):
        print(f"Environment {self.jid} is ready")
        await self.initiate()


