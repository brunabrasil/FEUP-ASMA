from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
from utils import haversine


class Drone(Agent):
    def __init__(self, jid, password, capacity, autonomy, velocity, latitude, longitude):
        super().__init__(jid, password)
        self.capacity = int(capacity[:-2])
        self.autonomy = int(autonomy[:-2])
        self.current_autonomy = self.autonomy
        self.velocity = float(velocity[:-3])
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.centers = dict()
        self.total_distance = 0
        self.total_time = 0

    async def setup(self):
        b = self.RecvBehav()
        template = Template()
        #template.set_metadata("performative", "propose")
        self.add_behaviour(b, template)
        self.inform_behav = self.InformBehav()
        

    def setCenters(self, center_id, center_lat, center_lon):
        self.centers[center_id] = (center_lat, center_lon)

    def goToCenter(self):
        self.current_autonomy = self.autonomy

    def deliverOrder(self, distance_to_center, total_distance_orders, latitude, longitude):
        self.goToCenter()
        self.current_autonomy -= total_distance_orders
        self.total_distance += distance_to_center + total_distance_orders
        self.total_time += (distance_to_center + total_distance_orders) * 1000 / self.velocity
        self.current_latitude = latitude
        self.current_longitude = longitude        

    def sendInfo(self):
        template = Template()
        #template.set_metadata("performative", "inform")
        self.add_behaviour(self.inform_behav, template)

    class RecvBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            approve_proposal = False
            if msg:
                if msg.metadata['performative'] == "propose":

                    orders = msg.body.split("order:")
                    orders = [item for item in orders if item != ""]
                    if('center1' in msg.sender):
                        sender = "center1"
                    else:
                        sender = "center2"
                    distance_to_center = haversine(self.agent.centers[sender][0], self.agent.centers[sender][1], self.agent.current_latitude, self.agent.current_longitude)
                    if (distance_to_center <= self.agent.current_autonomy):
                        total_distance = 0
                        total_capacity = 0

                        for i in range (0, len(orders)): # first one is a empty string
                            order = orders[i]
                            order = order.split("/")
                            total_capacity += int(order[3])
                            
                            if(i == 0):
                                distance_to_order = haversine(float(order[1]), float(order[2]), self.agent.centers[sender][0], self.agent.centers[sender][1])

                            else:
                                distance_to_order = haversine(float(order[1]), float(order[2]), float(orders[i-1].split("/")[1]),float(orders[i-1].split("/")[2]))
                            
                            total_distance += distance_to_order
                            if(i == len(orders) - 1):
                                distance_return_to_center1 = haversine(float(order[1]), float(order[2]), self.agent.centers['center1'][0], self.agent.centers['center1'][1])
                                distance_return_to_center2 = haversine(float(order[1]), float(order[2]), self.agent.centers['center2'][0], self.agent.centers['center2'][1])
                                if((total_distance + distance_return_to_center1 <= self.agent.autonomy or total_distance + distance_return_to_center2 <= self.agent.autonomy) and total_capacity <= self.agent.capacity):
                                    approve_proposal = True
                                    
                    msg = Message(to = str(msg.sender))
                    msg.sender = str(self.agent.jid)

                    if(approve_proposal):
                        msg.set_metadata("performative", "accept-proposal")
                        self.agent.deliverOrder(distance_to_center, total_distance, float(orders[len(orders)-1].split("/")[1]), float(orders[len(orders)-1].split("/")[2]))
                    
                    else:
                        msg.set_metadata("performative", "reject-proposal")  
                    
                    msg.body = ""
                    for order in orders:
                        msg.body += order.split("/")[0] + "/"
                    await self.send(msg)
                        
                    self.agent.sendInfo()
            else:
                print("Did not received any message after 10 seconds")
    
    class InformBehav(OneShotBehaviour):
        async def run(self):
            for center_id in self.agent.centers.keys():
                msg = Message(to= (center_id + "@localhost"))
                msg.set_metadata("performative", "inform")
                msg.body = "Hello World" 

                await self.send(msg)

            # stop agent from behaviour
            await self.agent.stop()



