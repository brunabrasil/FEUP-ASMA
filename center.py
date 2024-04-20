from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio

# Order class with its attributes
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
        self.drones_left = drones.copy() # Drones that havent respond to a request
        self.count_refuses = 0 # Number of refuses to a request
    
    # Add a order to the center
    def add_order(self, order_id, latitude, longitude, weight):
        order = Order(order_id, latitude, longitude, weight)
        self.orders[order_id] = order

    # Load the data from the dataframe to a list of instances of the class Order
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
        # Stop agent when all the orders are delivered
        async def on_end(self):
            await self.agent.stop()

        async def run(self):
            await asyncio.sleep(1)
            orders_selected = []
            
            # Select orders per order until the capacity of the drone can't take more 
            for order_id, order in self.agent.orders.items():
                total_weight = sum(order.weight for order in orders_selected)
                if (total_weight+order.weight) <= 20:
                    orders_selected.append(order)
                else:
                    break
            
            # If many refuses to a request, reduce number of orders -> reduce distance
            if(self.agent.count_refuses >= 4):
                orders_selected.pop()

            #format content string with the orders info
            content = ""
            print("\n")

            print("Request: ")
            for order in orders_selected:
                print(order.order_id)
                content += "order:" + str(order.order_id) + '/' +  str(order.latitude) + '/' +  str(order.longitude) + '/' +  str(order.weight)   

            msg = Message()
            msg.sender = str(self.agent.jid)
            msg.set_metadata("performative", "request") 
            msg.body = content

            # Send request to each drone
            for drone_id in self.agent.drones.keys():

                msg.to = drone_id + "@localhost"
                await self.send(msg)
                
                response_msg = await self.receive(timeout=10)
                
                if response_msg:
                    if(response_msg.body == str(-2)):
                        print(' - ' + drone_id + ' not available')
                    elif(response_msg.body == str(-1)):
                        print(' - ' + drone_id + ' cant make the delivery')
                    else:
                        print(' - ' + drone_id + ' time to deliver: ' + response_msg.body)
                    
                    if response_msg.metadata['performative'] == "refuse":
                        self.agent.responses[response_msg.sender] = float('inf')
                        if response_msg.body == "-1":
                            self.agent.count_refuses +=1

                    elif response_msg.metadata['performative'] == "agree":
                        self.agent.responses[response_msg.sender] = float(response_msg.body)
                        self.agent.count_refuses = 0
                else:
                    print("No response received")

            # Verify if has response of all drones
            if(len(self.agent.responses) == len(self.agent.drones)):
                # Choose drone that takes less time to deliver
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

                    await self.send(new_msg)
                
                # Start again the process to the next orders
                self.agent.responses = dict()
                self.agent.drones_left = self.agent.drones.copy()
            
            # When all orders are completed, inform the drones and stop its self
            if(len(self.agent.orders)== 0):
                print("\n")
                print(str(self.agent.jid).split("@")[0] + ' finished orders')
                print("\n")
                for drone_id in self.agent.drones.keys():
                    finish_msg = Message()
                    finish_msg.sender = str(self.agent.jid)
                    finish_msg.to = drone_id + "@localhost"
                    finish_msg.set_metadata("performative", "inform")
                    finish_msg.body = "Orders finished"
                    await self.send(finish_msg)
                
                finish_msg.to = "environment@localhost"
                await self.send(finish_msg)
                
                self.kill()
                    
        