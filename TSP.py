import itertools

"""
This function calculates the distance of a certain route
Receives the route and uses the distances in the matrix to calculate it
"""
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

# Example usage:
if __name__ == "__main__":
    # Row N indicates the distance from Node N to all other nodes
    distance_matrix = [
        [0, 5, 2, 7],
        [5, 0, 3, 8],
        [2, 3, 0, 6],
        [7, 8, 6, 0]
    ]

    best_route, shortest_distance = tsp_brute_force(distance_matrix)
    print("Best route:", best_route)
    print("Shortest distance:", shortest_distance)
