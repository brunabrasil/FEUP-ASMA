import math
import itertools

def haversine(lat1, lon1, lat2, lon2):
     
    # distance between latitudes
    # and longitudes
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0
 
    # convert to radians
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0
 
    # apply formulae
    a = (pow(math.sin(dLat / 2), 2) +
         pow(math.sin(dLon / 2), 2) *
             math.cos(lat1) * math.cos(lat2));
    rad = 6371
    c = 2 * math.asin(math.sqrt(a))
    return rad * c


# Calculates the distance of a certain route
def calculate_route_distance(route, distance_matrix):
    distance = 0
    for i in range(len(route) - 1):
        distance += distance_matrix[route[i]][route[i + 1]]
    return distance

"""
This function calculates the minimum distance
Starts by calculating all the possible routes (permutations)
Iterates through all of them, calculates the distance using the calculate_route_distance function
Checks if the current route is shorter than the last one and saves the shortest
"""
def tsp_brute_force(distance_matrix):
    num_nodes = len(distance_matrix)
    shortest_distance = float('inf')
    best_route = None

    for perm in itertools.permutations(range(1, num_nodes)):
        route = [0] + list(perm)  # Start at node 0
        distance = calculate_route_distance(route, distance_matrix)
        if distance < shortest_distance:
            shortest_distance = distance
            best_route = route

    return best_route, shortest_distance