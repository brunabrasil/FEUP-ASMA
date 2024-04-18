from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
from utils import haversine
from threading import Timer
import asyncio


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
        self.available = True
        self.accepted = dict()
        self.pending = dict()
        self.finished_centers = set()
        
    async def setup(self):
        rcv_propose = self.RecvProposes() # get proposals
        self.add_behaviour(rcv_propose)
        

    def set_centers(self, center_id, center_lat, center_lon):
        self.centers[center_id] = (center_lat, center_lon)

    def go_to_center(self):
        self.current_autonomy = self.autonomy

    def deliver_order(self, distance_to_center, total_distance_orders, latitude, longitude):
        self.go_to_center()
        self.current_autonomy -= total_distance_orders
        self.total_distance += distance_to_center + total_distance_orders
        self.total_time += (distance_to_center + total_distance_orders) * 1000 / self.velocity
        self.current_latitude = latitude
        self.current_longitude = longitude


    def calculate_duration(self, sender, orders):
        distance_to_center = haversine(self.centers[sender][0], self.centers[sender][1], self.current_latitude, self.current_longitude)
        total_orders_distance = 0
        if ( distance_to_center >= self.autonomy):
            return -1, 0, 0
        
        for i in range (0, len(orders)): # first one is a empty string
            order = orders[i]
            order = order.split("/")
            
            if(i == 0):
                distance_to_order = haversine(float(order[1]), float(order[2]), self.centers[sender][0], self.centers[sender][1])

            else:
                distance_to_order = haversine(float(order[1]), float(order[2]), float(orders[i-1].split("/")[1]),float(orders[i-1].split("/")[2]))
            
            total_orders_distance += distance_to_order
            
            if(i == len(orders) - 1):
                distance_return_to_center1 = haversine(float(order[1]), float(order[2]), self.centers['center1'][0], self.centers['center1'][1])
                distance_return_to_center2 = haversine(float(order[1]), float(order[2]), self.centers['center2'][0], self.centers['center2'][1])
          
        if ((total_orders_distance + distance_return_to_center1 <= self.autonomy )
            or (total_orders_distance + distance_return_to_center2 <= self.autonomy)): 
            duration = (total_orders_distance + distance_to_center) * 1000 / self.velocity    
            return duration, distance_to_center, total_orders_distance
        
        else:
            return -1, 0, 0


    class RecvProposes(CyclicBehaviour):
        async def on_end(self):
            print('morriiii')
            await self.agent.stop()
        async def run(self):
            msg = await self.receive(timeout=10) # wait for a request
            if msg:
                if msg.metadata['performative'] == "request":
                    if('center1' in msg.sender):
                        sender = "center1"
                    else:
                        sender = "center2"

                    orders = msg.body.split("order:")
                    orders = [item for item in orders if item != ""]
                    duration, distance_to_center, total_orders_distance = self.agent.calculate_duration(sender, orders) #calculate duration to deliver order(s)

 
                    send_msg = Message(to = (sender + "@localhost"))
                    send_msg.sender = str(self.agent.jid)
                    # respond refusing or agreeing to deliver
                    if(not self.agent.available):
                        send_msg.set_metadata("performative", "refuse")  
                        send_msg.body = str(-2)
                        await self.send(send_msg)

                    elif(duration == -1 ):
                        send_msg.set_metadata("performative", "refuse")  
                        send_msg.body = str(-1)
                        await self.send(send_msg)

                    else:
                        if (len(self.agent.accepted) > 0):
                            self.agent.pending[msg.sender] = (duration, distance_to_center, total_orders_distance, orders)
                        else:
                            send_msg.set_metadata("performative", "agree")
                            send_msg.body = str(duration)
                            self.agent.accepted[msg.sender] = (duration, distance_to_center, total_orders_distance, orders)
                            await self.send(send_msg)
                
                elif msg.metadata['performative'] == "inform":
                    if msg.body == "Deliver":
                        print("DELIVERED ORDERRRR")

                        (duration, distance_to_center, total_orders_distance, orders) = self.agent.accepted.pop(msg.sender)
                        self.agent.deliver_order(distance_to_center, total_orders_distance, float(orders[len(orders)-1].split("/")[1]), float(orders[len(orders)-1].split("/")[2]))
                        self.agent.available = False
                        print("Time: " + str(duration/100))
                        t = Timer(duration/100, self.set_available)
                        t.start()       
                        # recusar asque estao em pending
                        if (len(self.agent.pending) > 0):
                            center, (duration, distance_to_center, total_orders_distance, orders) = self.agent.pending.popitem()
                            send_msg = Message(to = center)
                            send_msg.sender = str(self.agent.jid)
                            send_msg.set_metadata("performative", "refuse")  
                            send_msg.body = str(-2)
                            await self.send(send_msg)
                    elif msg.body == "Don't deliver":
                        if (len(self.agent.accepted) > 0):
                            self.agent.accepted.pop(msg.sender) # remove accepted because not going to deliver
                        #enviar agree to pending
                        if (len(self.agent.pending) > 0):
                            center, (duration, distance_to_center, total_orders_distance, orders) = self.agent.pending.popitem()
                            
                            self.agent.accepted[center] = (duration, distance_to_center, total_orders_distance, orders)

                            send_msg = Message(to = center)
                            send_msg.sender = str(self.agent.jid)
                            send_msg.set_metadata("performative", "agree")
                            send_msg.body = str(duration)
                            await self.send(send_msg)
                    elif msg.body == "Orders finished":
                        self.agent.finished_centers.add(msg.sender)
                        if len(self.agent.finished_centers) == 1:
                            # retornar para casa :)
                            print(self.agent.total_time)
                            self.kill()
                        
            else:
                print("Did not received request after 10 seconds")
                
                
        def set_available(self):
            self.agent.available = True





