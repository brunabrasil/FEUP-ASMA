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
        self.latitude = center_info["latitude"]
        self.longitude = center_info["longitude"]
        df.drop(df.index[0], inplace=True)
        df.reset_index(drop=True, inplace=True)
        for index, row in df.iterrows():    
            self.add_order(row['id'], row['latitude'], row['longitude'], row['weight'])

    async def setup(self):
        # self.b = self.DroneInfo()
        # self.b.setDroneNumber(self.numDrones)
        # self.add_behaviour(self.b)
        self.add_behaviour(self.Behav1())
        print(f"Center {self.jid} is ready")
        self.load_drones()

    def load_drones(self):
        for drone in self.drones:
            for order in self.orders:
                if order.weight <= drone.capacity:
                    if drone.presence.is_available():

                        self.orders.remove(order)
                    break

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
    

    class Behav1(OneShotBehaviour):
        def on_available(self, jid, stanza):
            print("[{}] Agent {} is available.".format(self.agent.name, jid.split("@")[0]))

        def on_subscribed(self, jid):
            print("[{}] Agent {} has accepted the subscription.".format(self.agent.name, jid.split("@")[0]))
            print("[{}] Contacts List: {}".format(self.agent.name, self.agent.presence.get_contacts()))

        def on_subscribe(self, jid):
            print("[{}] Agent {} asked for subscription. Let's aprove it.".format(self.agent.name, jid.split("@")[0]))
            self.presence.approve(jid)

        async def run(self):
            self.presence.on_subscribe = self.on_subscribe
            self.presence.on_subscribed = self.on_subscribed
            self.presence.on_available = self.on_available

            self.presence.set_available()
            for drone in self.agent.drones:
                self.presence.subscribe(str(drone.jid))
            # print(self.presence.get_contacts())

            


        