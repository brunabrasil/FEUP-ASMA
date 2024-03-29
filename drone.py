from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template

class Drone(Agent):
    def __init__(self, jid, password, capacity, autonomy, velocity, initialPos, numCenters):
        super().__init__(jid, password)
        self.capacity = capacity
        self.autonomy = autonomy
        self.velocity = velocity
        self.current_location = initialPos
        self.destination = None
        self.numCenters = numCenters

    async def setup(self):
        print(f"Drone {self.jid} is ready")


    class RecvBehav(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=20) # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("ReceiverAgent started")
        b = self.RecvBehav()
        template = Template()
        template.set_metadata("performative", "query")
        self.add_behaviour(b, template)





