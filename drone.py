from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template
from utils import haversine
from threading import Timer
from TSP import tsp_brute_force


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
        self.available = True          # Set as true when the drone is ready to receive an order, set as false when the drone is  delivering an order
        self.accepted_message = dict() # Request that the drone has agreed to and is waiting for the confirm (if he is going to deliver or not)
        self.pending = dict()          # Request that the drone can do it but first is waiting to know the confirmation of a request that accepted so that it can agree/refuse the pending request
        self.finished_centers = set()  # Centers that dont have anymore orders
        self.min_time = float('inf')
        self.max_time = float('-inf')
        self.occupation = []
        self.current_capacity = 0

        
    async def setup(self):
        rcv_propose = self.DroneHandler()
        self.add_behaviour(rcv_propose)
        
    # Store the position of the centers
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

    # When it gets to the center, recharge its autonomy
    def go_to_center(self):
        self.current_autonomy = self.autonomy

    # Method to simulate delivering an order (latitude and longitude is the position of the last order to deliver)
    def deliver_order(self, distance_to_center, total_distance_orders, latitude, longitude):
        self.go_to_center()
        self.current_autonomy -= total_distance_orders
        self.total_distance += (distance_to_center + total_distance_orders)
        time_deliver = (distance_to_center + total_distance_orders) * 1000 / self.current_velocity
        self.total_time += time_deliver
        self.min_time = min(self.min_time, time_deliver)
        self.max_time = max(self.min_time, time_deliver)
        # Update current position
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.occupation.append(self.current_capacity / self.capacity)


    # Calculate the time and distance of delivering orders
    def calculate_duration(self, sender, orders):
        matrix = []
        distance_drone_to_center = haversine(self.centers[sender][0], self.centers[sender][1], self.current_latitude, self.current_longitude)
        # If the drone cant go to requested center, return -1
        if (distance_drone_to_center >= self.autonomy):
            return -1, 0, 0, 0
                
        # Creating distance matrix to aplly the Traveling Salesman Problem (TSP)
        # First row: center
        row = [0.0]
        for i in range (0, len(orders)):
            order_i = orders[i].split("/")
            distance_order_to_center = haversine(self.centers[sender][0], self.centers[sender][1], float(order_i[1]), float(order_i[2]))
            row.append(distance_order_to_center)
        
        matrix.append(row)
        self.current_capacity = 0
        # Rest of rows: orders
        for i in range (0, len(orders)):
            row = []
            order_i = orders[i]
            order_i = order_i.split("/")
            self.current_capacity += int(order_i[len(order_i)- 1])
            distance_order_to_center = haversine(self.centers[sender][0], self.centers[sender][1], float(order_i[1]), float(order_i[2]))
            row.append(distance_order_to_center)
            for j in range (0, len(orders)):
                order_j = orders[j].split("/")
                if i==j:
                    distance_order_to_order = 0.0
                else:
                    distance_order_to_order = haversine(float(order_i[1]), float(order_i[2]), float(order_j[1]), float(order_j[2]))
                row.append(distance_order_to_order)
            
            matrix.append(row)
            
        best_route, orders_shortest_distance = tsp_brute_force(matrix)
        
        last_order_index = best_route[-1] - 1
        last_order = orders[last_order_index].split("/")

        # Calculate distance of last order in the route
        distance_return_to_center1 = haversine(float(last_order[1]), float(last_order[2]), self.centers['center1'][0], self.centers['center1'][1])
        distance_return_to_center2 = haversine(float(last_order[1]), float(last_order[2]), self.centers['center2'][0], self.centers['center2'][1])
        
        # Verify if the drone has enough autonomy to deliver all order and return to a center
        if ((orders_shortest_distance + distance_return_to_center1 <= self.autonomy )
            or (orders_shortest_distance + distance_return_to_center2 <= self.autonomy)): 

            duration = (orders_shortest_distance + distance_drone_to_center) * 1000 / self.current_velocity    
            return duration, distance_drone_to_center, orders_shortest_distance, last_order_index
        
        else:
            return -1, 0, 0, 0

    # At the end, drone return to the closest center
    def return_to_a_center(self):
        distance_to_center1 = haversine(self.centers['center1'][0], self.centers['center1'][1], self.current_latitude, self.current_longitude)
        distance_to_center2 = haversine(self.centers['center2'][0], self.centers['center2'][1], self.current_latitude, self.current_longitude)
        
        self.total_distance += min(distance_to_center1, distance_to_center2)
        self.total_time += min(distance_to_center1, distance_to_center2) * 1000 / self.current_velocity
        

    class DroneHandler(CyclicBehaviour):
        #Stop agent when all orders in all centers are delivered
        async def on_end(self):
            print(str(self.agent.jid).split("@")[0] + ":")
            occupation_rate = sum(self.agent.occupation)/len(self.agent.occupation)
            print("Occupation rate: " + str(occupation_rate))
            print("Total time: " + str(self.agent.total_time))
            print("Min time: " + str(self.agent.min_time))
            print("Max time: " + str(self.agent.max_time))
            print("\n")
            await self.agent.stop()

        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                if msg.metadata['performative'] == "request": # Dealing with a request of a center
                    if('center1' in msg.sender):
                        sender = "center1"
                    else:
                        sender = "center2"

                    orders = msg.body.split("order:")
                    orders = [item for item in orders if item != ""]
                    duration, distance_to_center, total_orders_distance, last_order_index = self.agent.calculate_duration(sender, orders) #calculate duration to deliver order(s)

 
                    send_msg = Message(to = (sender + "@localhost"))
                    send_msg.sender = str(self.agent.jid)
                    
                    # Refuse if drone not available
                    if(not self.agent.available):
                        send_msg.set_metadata("performative", "refuse")  
                        send_msg.body = str(-2)
                        await self.send(send_msg)
                    
                    # Refuse if drone does not have enough autonomy to deliver the orders
                    elif(duration == -1 ):
                        send_msg.set_metadata("performative", "refuse")  
                        send_msg.body = str(-1)
                        await self.send(send_msg)

                    else:
                        # If already has agreed to other request, put on pending to wait to know what to do
                        if (len(self.agent.accepted_message) > 0):
                            self.agent.pending[msg.sender] = (duration, distance_to_center, total_orders_distance, orders[last_order_index].split("/"))
                        else:
                            # Respond agreeing to request
                            send_msg.set_metadata("performative", "agree")
                            send_msg.body = str(duration)
                            self.agent.accepted_message[msg.sender] = (duration, distance_to_center, total_orders_distance, orders[last_order_index].split("/"))
                            await self.send(send_msg)
                
                # Deal with confirm messages of centers
                elif msg.metadata['performative'] == "inform":
                    print(msg.sender)
                    # Deliver order that has accepted
                    if msg.body == "Deliver":
                        print(str(self.agent.jid).split("@")[0] + " delivering")

                        (duration, distance_to_center, total_orders_distance, last_order) = self.agent.accepted_message.pop(msg.sender)
                        self.agent.deliver_order(distance_to_center, total_orders_distance, float(last_order[1]), float(last_order[2]))
                        
                        # Put drone not available during the time (reduced) to deliver 
                        self.agent.available = False
                        t = Timer(duration/200, self.set_available)
                        t.start()

                        # Refuse pending orders because is occupied delivering the one that accepted
                        if (len(self.agent.pending) > 0):
                            center, (duration, distance_to_center, total_orders_distance, last_order) = self.agent.pending.popitem()
                            
                            send_msg = Message(to = str(center))
                            send_msg.sender = str(self.agent.jid)
                            send_msg.set_metadata("performative", "refuse")  
                            send_msg.body = str(-2)
                            await self.send(send_msg)

                    elif msg.body == "Don't deliver":
                        # Remove from accepted once since is not going to deliver that order
                        if (len(self.agent.accepted_message) > 0):
                            self.agent.accepted_message.pop(msg.sender)

                        # Send agree about pending order since is not occupied delivering the previous one
                        if (len(self.agent.pending) > 0):
                            center, (duration, distance_to_center, total_orders_distance, last_order) = self.agent.pending.popitem()
                            
                            self.agent.accepted_message[center] = (duration, distance_to_center, total_orders_distance, last_order)
                            
                            send_msg = Message(to = str(center))
                            send_msg.sender = str(self.agent.jid)
                            send_msg.set_metadata("performative", "agree")
                            send_msg.body = str(duration)
                            await self.send(send_msg)

                    # The center does not have anymore orders
                    elif msg.body == "Orders finished":
                        self.agent.finished_centers.add(msg.sender)

                        # Verify if all centers have finished
                        if len(self.agent.finished_centers) == 2:
                            # Return to a center
                            self.agent.return_to_a_center()
                            self.kill()

                    if "environment" in msg.sender:
                        print("Weather")
                        print(msg.body)
                        self.agent.set_weather(msg.body)

                        
            else:
                print("Did not received message after 10 seconds")
                
        # async call to this function to allow the agent to receive orders again 
        def set_available(self):
            self.agent.available = True



            
            