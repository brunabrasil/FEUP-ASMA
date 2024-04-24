from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random
from threading import Timer
import asyncio

class Environment(Agent):

    def __init__(self, jid, password, drones):
        super().__init__(jid, password)
        self.weather = ['sunny', 'raining', 'storm']
        self.drones = drones
        self.send_weather = True
        self.finished_centers = set()  # Centers that dont have anymore orders

    def random_weather(self):
        # Define the probabilities for each weather
        probabilities = [0.6, 0.3, 0.1]
        selected = random.choices(self.weather, weights=probabilities, k=1)
        return selected[0]
    
    class ResponseHandler(CyclicBehaviour):
        def set_available(self):
            self.agent.send_weather = True
        async def on_end(self):
            await self.agent.stop()

        async def run(self):
            
            if(self.agent.send_weather):
                weather = self.agent.random_weather()
                for drone_id in self.agent.drones.keys():
                    send_msg = Message(to = (drone_id + "@localhost"))
                    send_msg.sender = str(self.agent.jid)
                    send_msg.set_metadata("performative", "inform")
                    send_msg.body = weather
                    await self.send(send_msg)
                    
                self.agent.send_weather = False
                t = Timer(5, self.set_available)
                t.start()

            msg = await self.receive(timeout=10)
            if msg:
                if msg.metadata['performative'] == "inform" and msg.body == "Orders finished":
                    self.agent.finished_centers.add(msg.sender)
                    if len(self.agent.finished_centers) == 2:
                        self.kill()
                

    async def setup(self):
        res_weather = self.ResponseHandler()
        self.add_behaviour(res_weather)


