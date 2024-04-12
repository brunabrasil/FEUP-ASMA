from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template
from utils import haversine


class Drone(Agent):
    def __init__(self, jid, password, capacity, autonomy, velocity, latitude, longitude):
        super().__init__(jid, password)
        self.capacity = int(capacity[:-2])
        self.autonomy = int(autonomy[:-2])
        self.velocity = velocity
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.destination = None
        self.centers = dict()

    async def setup(self):
        b = self.RecvBehav()
        template = Template()
        template.set_metadata("performative", "propose")
        self.add_behaviour(b, template)

    def setCenters(self, center_id, center_lat, center_lon):
        self.centers[center_id] = (center_lat, center_lon)


    class RecvBehav(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                order = msg.body.split("/")
                if('center1' in msg.sender):
                    sender = "center1"
                else:
                    sender = "center2"
                
                distance_to_center = haversine(self.agent.centers[sender][0], self.agent.centers[sender][1], self.agent.current_latitude, self.agent.current_longitude)
                distance_to_order = haversine(float(order[1]), float(order[2]), self.agent.current_latitude, self.agent.current_longitude)
                distance_return_to_center1 = haversine(float(order[1]), float(order[2]), self.agent.centers['center1'][0], self.agent.centers['center1'][1])
                distance_return_to_center2 = haversine(float(order[1]), float(order[2]), self.agent.centers['center2'][0], self.agent.centers['center2'][1])

                total_distance1 = distance_to_center + distance_to_order + distance_return_to_center1
                total_distance2 = distance_to_center + distance_to_order + distance_return_to_center2

                print(msg.sender)
                msg = Message(to = str(msg.sender))
                msg.sender = str(self.agent.jid)
                if (int(order[3]) > self.agent.capacity):
                    print('nao')
                    msg.set_metadata("performative", "reject-proposal")  
                    msg.body = 'Reject'   
                elif (total_distance1 > self.agent.autonomy):
                    print('nao')
                    msg.set_metadata("performative", "reject-proposal") 
                    msg.body = 'Reject'   
                     
                elif (total_distance2 > self.agent.autonomy):
                    print('nao')
                    msg.set_metadata("performative", "reject-proposal") 
                    msg.body = 'Reject'   
                else:
                    print('going to deliver')
                    msg.set_metadata("performative", "accept-proposal")
                    msg.body = 'Accept'   


                    # call function to deliver
                await self.send(msg)
                

            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            await self.agent.stop()








