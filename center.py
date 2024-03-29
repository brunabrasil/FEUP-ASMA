from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
import pandas as pd

class Order:
    def __init__(self, order_id, latitude, longitude, weight):
        self.order_id = order_id
        self.latitude = latitude
        self.longitude = longitude
        self.weight = weight


class Center(Agent):
    def __init__(self, jid, password, df, numDrones):
        super().__init__(jid, password)
        self.orders = []
        self.load_csv(df)
        self.drones = []
        self.numDrones = numDrones
        
            

    def add_order(self, order_id, latitude, longitude, weight):
        order = Order(order_id, latitude, longitude, weight)
        self.orders.append(order)

    def load_csv(self, df):
        center_info = df.iloc[0]
        self.center_id = center_info["id"]
        self.latitude = center_info["latitude"]
        self.longitude = center_info["longitude"]
        df.drop(df.index[0], inplace=True)
        df.reset_index(drop=True, inplace=True)
        for index, row in df.iterrows():    
            self.add_order(row['id'], row['latitude'], row['longitude'], row['weight'])

    async def setup(self):
        self.b = self.DroneInfo()
        self.b.setDroneNumber(self.numDrones)
        self.add_behaviour(self.b)
        print(f"Center {self.jid} is ready")

    class DroneInfo(OneShotBehaviour):
        async def run(self):
            for i in range(1, self.numDrones+1):
                receiver = "drone" + str(i) + "@localhost"
                msg = Message(to=receiver)
                msg.set_metadata("performative", "query")  
                # msg.set_metadata("ontology", "droneInfo")  
                # msg.set_metadata("language", "OWL-S")      
                msg.body = "drone" + str(i) + " Info"                    

                await self.send(msg)
                print("Message sent!")

        def setDroneNumber(self, numDrones):
            self.numDrones = numDrones


        