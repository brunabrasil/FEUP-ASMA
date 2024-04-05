from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template



class Drone(Agent):
    def __init__(self, jid, password, capacity, autonomy, velocity, initialPos, numCenters):
        super().__init__(jid, password)
        self.capacity = int(capacity[:-2])
        self.autonomy = int(autonomy[:-2])
        self.velocity = velocity
        self.current_location = initialPos
        self.destination = None
        self.numCenters = numCenters

    async def setup(self):
        print(f"Drone {self.jid} is ready")
        self.add_behaviour(self.Presence())


    # class RecvBehav(OneShotBehaviour):
    #     async def run(self):
    #         msg = await self.receive(timeout=20) # wait for a message for 10 seconds
    #         if msg:
    #             print("Message received with content: {}".format(msg.body))
    #         else:
    #             print("Did not received any message after 10 seconds")

    #         # stop agent from behaviour
    #         await self.agent.stop()

    # async def setup(self):
    #     print("ReceiverAgent started")
    #     b = self.RecvBehav()
    #     template = Template()
    #     template.set_metadata("performative", "query")
    #     self.add_behaviour(b, template)


    class Presence(OneShotBehaviour):
        def on_available(self, jid, stanza):
            print("[{}] Agent {} is available.".format(self.agent.name, jid.split("@")[0]))

        def on_subscribed(self, jid):
            print("[{}] Agent {} has accepted the subscription.".format(self.agent.name, jid.split("@")[0]))
            print("[{}] Contacts List: {}".format(self.agent.name, self.agent.presence.get_contacts()))

        def on_subscribe(self, jid):
            print("[{}] Agent {} asked for subscription. Let's aprove it.".format(self.agent.name, jid.split("@")[0]))
            self.presence.approve(jid)
            self.presence.subscribe(jid)

        async def run(self):
            self.presence.set_available()
            self.presence.on_subscribe = self.on_subscribe
            self.presence.on_subscribed = self.on_subscribed
            self.presence.on_available = self.on_available




