import time, math
from heapq import heapify, heappop, heappush
import EVE_DAO.models as eve

STAGING_NAME = 'Turnur - Ripley\'s Kennel and Playhouse'

class Dijkstra_entry:
    def __init__(self):
        self.dist = math.inf
        self.previous = None
        self.visited = False
    def __repr__(self):
        return (f'Dist:{self.dist} | Previous:{self.previous} | Visited:{self.visited}')

def find_system(search, systems: list[eve.System]) -> eve.System:
    for system in systems:
        if type(search) == str:
            if system.name == search:
                return system
        elif type(search) == int:
            if system.pk == search:
                return system
        else:
            break
    return None

def build_dijkstra_map(origin: eve.System, systems: list[eve.System]) -> dict[int, Dijkstra_entry]:
    dijkstra_map = {}
    systems_map = {}
    for system in systems:
        dijkstra_map[system.pk] = Dijkstra_entry()
        systems_map[system.pk] = system
    dijkstra_map[origin.pk].dist = 0
    dijkstra_map[origin.pk].previous = None
    priority_queue = [(dijkstra_map[origin.pk].dist, origin.pk)]
    heapify(priority_queue)
    while priority_queue:
        current_system = systems_map[heappop(priority_queue)[1]]
        if dijkstra_map[current_system.pk].visited:
            continue
        dijkstra_map[current_system.pk].visited = True
        for connected_system_id in current_system.stargates:
            weight = 1
            new_distance = dijkstra_map[current_system.pk].dist + weight
            if new_distance < dijkstra_map[connected_system_id].dist:
                dijkstra_map[connected_system_id].dist = new_distance
                dijkstra_map[connected_system_id].previous = current_system.pk
        for connected_system_id in current_system.stargates:
            if not dijkstra_map[connected_system_id].visited:
                heappush(priority_queue, (dijkstra_map[connected_system_id].dist, connected_system_id))
    return dijkstra_map

def find_route(origin: eve.System, destination: eve.System,
               dijkstra_map: dict[int, Dijkstra_entry], systems: list[eve.System]) -> list[eve.System]:
    route = []
    current_system = destination
    while current_system != origin:
        route.append(current_system)
        previous = find_system(dijkstra_map[current_system.pk].previous, systems)
        if previous is not None:
            current_system = previous
        else:
            current_system = origin
    route.append(current_system)
    route.reverse()
    return route

def optimize_routes(destinations: list[(eve.System, str)], distance_map: dict[int, dict[int, int]],
                    max_destination_per_route: int = 8) -> list[list[(eve.System, str)]]:
    routes = []
    staging, staging_name = destinations[0]
    destinations.pop(0)
    route_index = 0
    while destinations:
        i = 0
        max_distance = 0
        max_index = None
        target = None
        for destination, drill_name in destinations:
            distance = distance_map[staging.pk][destination.pk]
            if distance > max_distance:
                max_distance = distance
                target = (destination, drill_name)
                max_index = i
            i += 1
        routes.append([target])
        destinations.pop(max_index)

        while len(routes[route_index]) < max_destination_per_route:
            i = 0
            min_distance = math.inf
            min_index = None
            target = None
            for destination, drill_name in destinations:
                distance = distance_map[routes[route_index][0][0].pk][destination.pk]
                if distance < min_distance:
                    min_distance = distance
                    target = (destination, drill_name)
                    min_index = i
                i += 1

            if min_distance > max_distance:
                break
            routes[route_index].append(target)
            destinations.pop(min_index)
        route_index += 1

    return routes

def main(verbose:bool = False):
    systems: list[eve.System] = eve.get_systems(eve.Galaxy.NEW_EDEN, verbose=verbose)
    staging: eve.System = find_system(STAGING_NAME.split(' - ')[0], systems)
    destinations: list[(eve.System, str)] = [(staging, STAGING_NAME)]
    with open('metenox_drill_list') as drill_list:
        for drill_name in drill_list:
            drill_name = drill_name.strip('\n')
            system_name = drill_name.split(' - ')[0]
            destinations.append((find_system(system_name, systems), drill_name))

    dijkstra_maps: dict[int, dict[int, Dijkstra_entry]] = {}
    for system in systems:
        dijkstra_maps[system.pk] = {}
    if verbose:
        i = 1
        start_time = time.time()
    for destination in destinations:
        if verbose:
            print(f' Building dijkstra maps: {i}/{len(destinations)}', end='\r')
            i += 1
        system = destination[0]
        if not dijkstra_maps[system.pk]:
            dijkstra_maps[system.pk] = build_dijkstra_map(system, systems)
    if verbose:
        exectime = round(time.time() - start_time, 2)
        print('                                                                             ', end='\r')
        print(f'Building dijkstra maps: {i-1}/{len(destinations)}\texec time: {exectime}s')

    if verbose:
        i = 1
        start_time = time.time()
    distance_map: dict[int, dict[int, int]] = {}
    for origin, origin_drill_name in destinations:
        try:
            if distance_map[origin.pk]:
                if verbose: i += len(destinations)
                continue
        except KeyError:
            distance_map[origin.pk] = {}
        for destination, destination_drill_name in destinations:
            if verbose:
                print(f' Building distance maps: {i}/{len(destinations)**2}', end='\r')
                i += 1
            try:
                if distance_map[origin.pk][destination.pk]:
                    continue
            except KeyError:
                pass
            route = find_route(origin, destination, dijkstra_maps[origin.pk], systems)
            distance = len(route)
            distance_map[origin.pk][destination.pk] = distance
    if verbose:
        exectime = round(time.time() - start_time, 2)
        print('                                                                             ', end='\r')
        print(f'Building distance maps: {i-1}/{len(destinations)**2}\texec time: {exectime}s')

    routes = optimize_routes(destinations, distance_map)
    print(f'Number of routes: {len(routes)}')
    drill_qty = 0
    for route in routes:
        for drill in route:
            drill_qty += 1
    print(f'Number of drill visited: {drill_qty}')
    with open ('routes', 'w') as f:
        for route in routes:
            for system, drill_name in route:
                f.write(drill_name + '\n')
            f.write(f'----- {len(route)} -----\n')

if __name__ == '__main__':
    main(verbose=True)
