from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
from utils import haversine
import asyncio


class Drone(Agent):
    def __init__(self, jid, password, capacity, autonomy, velocity, latitude, longitude):
        super().__init__(jid, password)
        self.capacity = int(capacity[:-2])
        self.autonomy = int(autonomy[:-2])
        self.current_autonomy = self.autonomy
        self.velocity = float(velocity[:-3])
        self.current_velocity = self.velocity
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.centers = dict()
        self.total_distance = 0
        self.total_time = 0
        self.received_proposes = dict()
        

    async def setup(self):
        print('drone setup')
        #while(True):

        self.rcv_weather = self.RecvWeather() # get weather
        template_weather = Template()
        self.add_behaviour(self.rcv_weather, template_weather)
            
            # self.inform_availability = self.InformAvailability() # inform that is available
            # self.add_behaviour(self.inform_availability)

            # rcv_propose = self.RecvProposes() # get proposals
            # template = Template()
            # template.set_metadata("performative", "propose")
            # self.add_behaviour(rcv_propose, template)

            # choose_proposal = self.ChooseProposal() # choose proposal
            # self.add_behaviour(choose_proposal)
        

    def set_centers(self, center_id, center_lat, center_lon):
        self.centers[center_id] = (center_lat, center_lon)
        

    def set_weather(self, weather):
        self.weather = weather
        if weather == "sunny":
            self.current_velocity = self.velocity
        elif weather == "raining":
            self.current_velocity = self.velocity * 0.7
        elif weather == "storm":
            self.current_velocity = self.velocity * 0.5

    def go_to_center(self):
        self.current_autonomy = self.autonomy

    def deliver_order(self, distance_to_center, total_distance_orders, latitude, longitude):
        self.go_to_center()
        self.current_autonomy -= total_distance_orders
        self.total_distance += distance_to_center + total_distance_orders
        self.total_time += (distance_to_center + total_distance_orders) * 1000 / self.current_velocity
        self.current_latitude = latitude
        self.current_longitude = longitude
        

    class RecvProposes(CyclicBehaviour):
        async def run(self):
            self.agent.inform_availability.join() # wait to tell centers that its available
            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                if msg.metadata['performative'] == "propose":
                    if('center1' in msg.sender):
                        sender = "center1"
                    else:
                        sender = "center2"

                    orders = msg.body.split("order:")
                    orders = [item for item in orders if item != ""]

                    self.agent.received_proposes[sender] = orders

                    if set(self.agent.received_proposes.keys()) == set(self.agent.centers.keys()):
                        self.agent.received_proposes = dict()
                        await self.agent.stop()                     
                    
            else:
                print("Did not received any message after 10 seconds")

    class ChooseProposal(OneShotBehaviour):

        async def run(self):
            self.agent.rcv_propose.join() ## wait for the 
            orders_distance = dict()
            for center_id, orders in self.agent.received_proposes.items():

                distance_to_center = haversine(self.agent.centers[center_id][0], self.agent.centers[center_id][1], self.agent.current_latitude, self.agent.current_longitude)
                if (distance_to_center <= self.agent.current_autonomy):
                    total_distance = 0
                    total_capacity = 0

                    for i in range (0, len(orders)): # first one is a empty string
                        order = orders[i]
                        order = order.split("/")
                        total_capacity += int(order[3])
                        
                        if(i == 0):
                            distance_to_order = haversine(float(order[1]), float(order[2]), self.agent.centers[center_id][0], self.agent.centers[center_id][1])

                        else:
                            distance_to_order = haversine(float(order[1]), float(order[2]), float(orders[i-1].split("/")[1]),float(orders[i-1].split("/")[2]))
                        
                        total_distance += distance_to_order
                        if(i == len(orders) - 1):
                            distance_return_to_center1 = haversine(float(order[1]), float(order[2]), self.agent.centers['center1'][0], self.agent.centers['center1'][1])
                            distance_return_to_center2 = haversine(float(order[1]), float(order[2]), self.agent.centers['center2'][0], self.agent.centers['center2'][1])
                            if((total_distance + distance_return_to_center1 <= self.agent.autonomy or total_distance + distance_return_to_center2 <= self.agent.autonomy) and total_capacity <= self.agent.capacity):                    
                                orders_distance[center_id] = total_distance

            minimum_proposal_center = min(orders_distance, key=orders_distance.get)
            print(orders_distance)

            for center_id in self.agent.received_proposes.keys():
                msg = Message(to = (center_id + "@localhost"))
                msg.sender = str(self.agent.jid)
                if center_id == minimum_proposal_center:
                    msg.set_metadata("performative", "accept-proposal")
                    self.agent.deliver_order(distance_to_center, total_distance, float(orders[len(orders)-1].split("/")[1]), float(orders[len(orders)-1].split("/")[2]))
            
                else:
                    msg.set_metadata("performative", "reject-proposal")  
            
                msg.body = ""
                for order in orders:
                    msg.body += order.split("/")[0] + "/"

                await self.send(msg)
            
            await self.agent.stop()

                        
    class InformAvailability(OneShotBehaviour):
        async def run(self):
            self.agent.rcv_weather.join() # wait to know the weather

            for center_id in self.agent.centers.keys():
                msg = Message(to= (center_id + "@localhost"))
                msg.set_metadata("performative", "inform")
                msg.body = self.agent.weather

                await self.send(msg)

            # stop agent from behaviour
            await self.agent.stop()


    class RecvWeather(OneShotBehaviour):
        async def run(self):

            print('ask weather')

            msg = Message(to="environment@localhost")
            msg.set_metadata("performative", "query")
            msg.body = "Weather" 

            await self.send(msg)


            response_msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if response_msg:
                self.agent.set_weather(response_msg.body)
            else:
                self.agent.set_weather("sunny")
            
            # stop agent from behaviour
            await self.agent.stop()




