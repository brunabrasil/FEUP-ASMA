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
        self.pending = False


class Center(Agent):
    def __init__(self, jid, password, df, drones):
        super().__init__(jid, password)
        self.orders = dict()
        self.load_data(df)
        self.drones = drones
        
    def add_order(self, order_id, latitude, longitude, weight):
        order = Order(order_id, latitude, longitude, weight)
        self.orders[order_id] = order

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

        response_handler = self.ResponseHandler()
        self.add_behaviour(response_handler)

    def assign_orders(self, drone_id):
        capacity = self.drones[drone_id].capacity
        orders_selected = list()
        for orderId in self.orders.keys():
            order = self.orders[orderId]
            if(not order.pending):
                if(capacity - order.weight >= 0):
                    capacity -= order.weight
                    order.pending = True
                    orders_selected.append(order)
                    
            if(capacity == 0):
                break
        return orders_selected


    class ResponseHandler(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # Adjust timeout as needed
            if msg:
                order_ids = msg.body.split("/")
                order_ids = [item for item in order_ids if item != ""]
                print(msg.metadata['performative'])
                print(msg.sender)
                if msg.metadata['performative'] == "reject-proposal":
                    for order_id in order_ids:
                        self.agent.orders[order_id].pending = False

                elif msg.metadata['performative'] == "accept-proposal":
                    for order_id in order_ids:
                        self.agent.orders.pop(order_id)

                elif msg.metadata['performative'] == "inform":
                    drone_id = str(msg.sender).split("@")[0]
                    orders_selected = self.agent.assign_orders(drone_id)

                    msg = Message()
                    msg.sender = str(self.agent.jid)
                    msg.to = drone_id + "@localhost"
                    msg.set_metadata("performative", "propose") 
                    content = ""
                    for order in orders_selected:
                        content += "order:" + str(order.order_id) + '/' +  str(order.latitude) + '/' +  str(order.longitude) + '/' +  str(order.weight)   
                    msg.body = content   
                    await self.send(msg)

            else:
                print("No response received")

        