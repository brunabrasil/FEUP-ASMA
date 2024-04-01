import pandas as pd
import numpy as np
from haversine import haversine

# Function to calculate distance between two points
def calculate_distance(lat1, lon1, lat2, lon2):
    return haversine((lat1, lon1), (lat2, lon2))

# Function to load data from CSV files
def load_data(center_file, drone_file):
    centers = pd.read_csv(center_file, sep=';')
    drones = pd.read_csv(drone_file, sep=';')
    return centers, drones

# Function to find the nearest center for a given drone
def find_nearest_center(drone, centers):
    min_distance = np.inf
    nearest_center = None
    for index, center in centers.iterrows():
        distance = calculate_distance(drone['latitude'], drone['longitude'], center['latitude'], center['longitude'])
        if distance < min_distance:
            min_distance = distance
            nearest_center = center
    return nearest_center

# Function to select packages for delivery
def select_packages(center, drone, remaining_capacity):
    selected_packages = []
    for index, row in center.iterrows():
        if row['id'].startswith('order'):
            if row['weight'] <= remaining_capacity:
                selected_packages.append(row)
                remaining_capacity -= row['weight']
    return selected_packages

# Function to simulate drone delivery
def simulate_delivery(centers, drones):
    for index, drone in drones.iterrows():
        print(f"Drone {drone['id']} at {drone['initialPos']}:")
        current_center = find_nearest_center(drone, centers)
        remaining_capacity = drone['capacity']
        while remaining_capacity > 0:
            selected_packages = select_packages(current_center, drone, remaining_capacity)
            if len(selected_packages) == 0:
                break
            print(f"   Picked up packages: {[pkg['id'] for pkg in selected_packages]}")
            for pkg in selected_packages:
                centers = centers.drop(centers[centers['id'] == pkg['id']].index)
            remaining_capacity -= sum(pkg['weight'] for pkg in selected_packages)
            print(f"   Remaining capacity: {remaining_capacity}kg")
            nearest_center = find_nearest_center(drone, centers)
            distance_to_travel = calculate_distance(current_center['latitude'], current_center['longitude'],
                                                    nearest_center['latitude'], nearest_center['longitude'])
            time_to_travel = distance_to_travel / drone['velocity']
            remaining_autonomy = drone['autonomy'] - time_to_travel
            if remaining_autonomy < 0:
                print("   Drone needs to return to recharge.")
                remaining_autonomy = drone['autonomy']
            print(f"   Autonomy remaining: {remaining_autonomy}km")
            current_center = nearest_center
        print()

# Main function
def main():
    center1, center2 = load_data('center1.csv', 'center2.csv')
    centers = pd.concat([center1, center2], ignore_index=True)
    drones = pd.read_csv('drones.csv', sep=';')
    simulate_delivery(centers, drones)

if __name__ == "__main__":
    main()
