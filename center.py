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
        self.load_data(df)
        self.drones = drones
        
    def add_order(self, order_id, latitude, longitude, weight):
        order = Order(order_id, latitude, longitude, weight)
        self.orders.append(order)

    def load_data(self, df):
        center_info = df.iloc[0]
        self.center_id = center_info["id"]
        self.latitude = float(center_info["latitude"].replace(',', '.'))
        self.longitude = float(center_info["longitude"].replace(',', '.'))
        df.drop(df.index[0], inplace=True)
        df.reset_index(drop=True, inplace=True)
        for index, row in df.iterrows():    
            self.add_order(row['id'], float(row['latitude'].replace(',', '.')), float(row['longitude'].replace(',', '.')), row['weight'])

    async def setup(self):
        first_iteration = self.FirstIteration()
        first_iteration.setInfo(self.drones, self.orders)
        self.add_behaviour(first_iteration)

        template = Template()
        #template.set_metadata("performative", "propose")
        response_handler = self.ResponseHandler()
        self.add_behaviour(response_handler, template)

    class FirstIteration(OneShotBehaviour):
        async def run(self):
            assigned_drones = set()

            for order in self.orders[:4]:
                for drone in self.drones:
                    if drone.jid in assigned_drones:
                        continue
                    receiver = str(drone.jid)
                    msg = Message()
                    msg.sender = str(self.agent.jid)
                    msg.to = receiver
                    msg.set_metadata("performative", "propose")    
                    msg.body = str(order.order_id) + '/' +  str(order.latitude) + '/' +  str(order.longitude) + '/' +  str(order.weight)   
                    await self.send(msg)
                    print("Message sent!")
                    assigned_drones.add(drone.jid)  # Mark the order as assigned
                    break
            
        def setInfo(self, drones, orders):
            self.drones = drones
            self.orders = orders

    class ResponseHandler(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # Adjust timeout as needed
            if msg:
                print(f"Received message: {msg.body}")
                # Here you can parse the message and take appropriate actions based on the response
            else:
                print("No response received")



            


        