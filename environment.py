import pandas as pd
from drone import Drone
from center import Center
from spade.agent import Agent

class Environment(Agent):

    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.drones = dict()
        
    # Method to initialize the environment (drones and centers)
    async def initiate(self):
        # Read center and drones csv into a dataframe
        df_center1 = pd.read_csv("data/delivery_center1.csv", delimiter=";")
        df_center2 = pd.read_csv("data/delivery_center2.csv", delimiter=";")
        df_drones = pd.read_csv("data/delivery_drones.csv", delimiter=";")

        # Get the coordinates of the centers
        center1_lat = float(df_center1.iloc[0]['latitude'].replace(',', '.'))
        center1_lon = float(df_center1.iloc[0]['longitude'].replace(',', '.'))
        center2_lat = float(df_center2.iloc[0]['latitude'].replace(',', '.'))
        center2_lon = float(df_center2.iloc[0]['longitude'].replace(',', '.'))

        for index, row in df_drones.iterrows():
            # get the coordinates of the drones according to the center in which they are    
            if(row['initialPos'] == 'center1'):
                lat = center1_lat
                lon = center1_lon
            elif(row['initialPos'] == 'center2'):
                lat = center2_lat
                lon = center2_lon

            # Create the drones
            drone = Drone(row['id'] + "@localhost", "password", row['capacity'], row['autonomy'], row['velocity'], lat, lon)
            
            # Let drones know the centers position
            drone.set_centers('center1', center1_lat, center1_lon)
            drone.set_centers('center2', center2_lat, center2_lon)

            await drone.start()
            self.drones[row["id"]] = drone

        # Create the centers
        center1 = Center("center1@localhost", "password", df_center1, self.drones)
        await center1.start()

        center2 = Center("center2@localhost", "password", df_center2, self.drones)
        await center2.start()

        # await spade.wait_until_finished(center1)
        # await center1.stop()

    
    async def setup(self):
        await self.initiate()

    


