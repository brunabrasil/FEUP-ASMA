import pandas as pd
import spade
from drone import Drone
from center import Center
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
import random

drones = []
centers = []

class Environment(Agent):

    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.drones = dict()
        self.weather = ['sunny', 'raining', 'storm']

    def random_weather(self):
        # Define the probabilities for each weather
        probabilities = [0.6, 0.3, 0.1]
        selected = random.choices(self.weather, weights=probabilities, k=1)
        return selected[0]
        

    async def initiate(self):
        df_center1 = pd.read_csv("data/delivery_center1.csv", delimiter=";")
        df_center2 = pd.read_csv("data/delivery_center2.csv", delimiter=";")
        df_drones = pd.read_csv("data/delivery_drones.csv", delimiter=";")

        center1_lat = float(df_center1.iloc[0]['latitude'].replace(',', '.'))
        center1_lon = float(df_center1.iloc[0]['longitude'].replace(',', '.'))
        center2_lat = float(df_center2.iloc[0]['latitude'].replace(',', '.'))
        center2_lon = float(df_center2.iloc[0]['longitude'].replace(',', '.'))

        for index, row in df_drones.iterrows():    
            # Create an instance of the Drone class using the extracted information

            if(row['initialPos'] == 'center1'):
                lat = center1_lat
                lon = center1_lon
            elif(row['initialPos'] == 'center2'):
                lat = center2_lat
                lon = center2_lon

            
            drone = Drone(row['id'] + "@localhost", "password", row['capacity'], row['autonomy'], row['velocity'], lat, lon)
            
            drone.set_centers('center1', center1_lat, center1_lon)
            drone.set_centers('center2', center2_lat, center2_lon)

            await drone.start()
            self.drones[row["id"]] = drone
    
        center1 = Center("center1@localhost", "password", df_center1, self.drones)
        await center1.start()

        # center2 = Center("center2@localhost", "password", df_center2, self.drones)
        # await center2.start()

        # await spade.wait_until_finished(center1)
        # await center1.stop()

    
    async def setup(self):
        await self.initiate()

    


