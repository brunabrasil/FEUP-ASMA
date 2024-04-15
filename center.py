from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
import pandas as pd
import asyncio

class Order:
    def __init__(self, order_id, latitude, longitude, weight):
        self.order_id = order_id
        self.latitude = latitude
        self.longitude = longitude
        self.weight = weight


class Center(Agent):
    def __init__(self, jid, password, df, drones):
        super().__init__(jid, password)
        self.orders = dict()
        self.load_data(df)
        self.drones = drones
        self.responses = dict()
        self.drones_left = drones.copy()
        
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

    class ResponseHandler(CyclicBehaviour):
        async def run(self):
            
            orders_selected = []
            for order_id, order in self.agent.orders.items():
                total_weight = sum(order.weight for order in orders_selected)
                if total_weight+order.weight <= 20:
                    orders_selected.append(order)
                else:
                    break
            
            content = ""
            for order in orders_selected:
                content += "order:" + str(order.order_id) + '/' +  str(order.latitude) + '/' +  str(order.longitude) + '/' +  str(order.weight)   

        
            msg = Message()
            msg.sender = str(self.agent.jid)
            msg.set_metadata("performative", "request") 
            msg.body = content

            for drone_id in self.agent.drones.keys():
                print(drone_id)
                msg.to = drone_id + "@localhost"
                await self.send(msg)
                print("\n")
                response_msg = await self.receive(timeout=10)  # Adjust timeout as needed
                
                if response_msg:
                    print("response:")
                    print(response_msg)
                    print("\n")

                    if response_msg.metadata['performative'] == "refuse":
                        self.agent.responses[response_msg.sender] = float('inf')

                    elif response_msg.metadata['performative'] == "agree":
                        self.agent.responses[response_msg.sender] = float(response_msg.body)

            if(len(self.agent.responses) == len(self.agent.drones)):
                

                minimum_time_drone = min(self.agent.responses, key=self.agent.responses.get)
                for drone_id in self.agent.drones.keys():
                    new_msg = Message()
                    new_msg.sender = str(self.agent.jid)
                    new_msg.set_metadata("performative", "inform") 
                    new_msg.to = drone_id + "@localhost"
                    if (str(minimum_time_drone) == (drone_id + "@localhost")):
                        if(self.agent.responses[minimum_time_drone] != float('inf')):
                            new_msg.body = "Deliver"

                            for order in orders_selected:
                                self.agent.orders.pop(order.order_id)
                        else:
                            new_msg.body = "Don't deliver"

                    else:
                        new_msg.body = "Don't deliver"
                    print("MESSAGE")
                    print(drone_id)
                    print(new_msg.body)
                    print("\n")

                    await self.send(new_msg)

                self.agent.responses = dict()
                self.agent.drones_left = self.agent.drones.copy()

                await asyncio.sleep(1)
                    

            else:
                print("No response received")

        