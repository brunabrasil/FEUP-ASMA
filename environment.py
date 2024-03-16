import pandas as pd
import spade

df_center1 = pd.read_csv("data/delivery_center1.csv", delimiter=";")
df_center2 = pd.read_csv("data/delivery_center2.csv", delimiter=";")
df_drones = pd.read_csv("data/delivery_drones.csv")

# Get center info and remove it from the dataframe
center1_info = df_center1.iloc[0]
df_center1.drop(df_center1.index[0], inplace=True)
df_center1.reset_index(drop=True, inplace=True)

print(center1_info)

center2_info = df_center2.iloc[0]
df_center2.drop(df_center2.index[0], inplace=True)
df_center2.reset_index(drop=True, inplace=True)