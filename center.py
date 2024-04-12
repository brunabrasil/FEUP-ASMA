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
    def __init__(self, jid, password, df, drones):
        super().__init__(jid, password)
        self.orders = []
        self.load_csv(df)
        self.drones = drones
        
    def add_order(self, order_id, latitude, longitude, weight):
        order = Order(order_id, latitude, longitude, weight)
        self.orders.append(order)

    def load_csv(self, df):
        center_info = df.iloc[0]
        self.center_id = center_info["id"]
        self.latitude = float(center_info["latitude"].replace(',', '.'))
        self.longitude = float(center_info["longitude"].replace(',', '.'))
        df.drop(df.index[0], inplace=True)
        df.reset_index(drop=True, inplace=True)
        for index, row in df.iterrows():    
            self.add_order(row['id'], float(row['latitude'].replace(',', '.')), float(row['longitude'].replace(',', '.')), row['weight'])

    async def setup(self):
        print(f"Center {self.jid} is ready")
        self.b = self.DroneInfo()
        self.b.setInfo(self.drones, self.orders)
        self.add_behaviour(self.b)
        #self.load_drones()

    def load_drones(self):
        for drone in self.drones:
            for order in self.orders:
                if order.weight <= drone.capacity:
                    if drone.presence.is_available():

                        self.orders.remove(order)
                    break

    class DroneInfo(OneShotBehaviour):
        async def run(self):
            for drone in self.drones:
                receiver = str(drone.jid)
                msg = Message()
                msg.sender = str(self.agent.jid)
                msg.to = receiver
                msg.set_metadata("performative", "propose")  
                # msg.set_metadata("ontology", "droneInfo")  
                # msg.set_metadata("language", "OWL-S")      
                msg.body = str(self.orders[0].order_id) + '/' +  str(self.orders[0].latitude) + '/' +  str(self.orders[0].longitude) + '/' +  str(self.orders[0].weight )   
                await self.send(msg)
                print("Message sent!")
            
        def setInfo(self, drones, orders):
            self.drones = drones
            self.orders = orders



            


        