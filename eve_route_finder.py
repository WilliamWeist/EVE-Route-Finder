import time, math, sys
from heapq import heapify, heappop, heappush
import config
import EVE_DAO.models as eve
import William_ESI_Gateway.ESI_gateway as esi

STAGING_NAME = 'Turnur - Ripley\'s Kennel and Playhouse'
client_id = config.client_id
client_secret = config.client_secret
callback_url = config.callback_url
scopes = config.scopes

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

def build_routes(verbose:bool = False):
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

def load_routes() -> list[list[str]]:
    routes = []
    routes.append([])
    index = 0
    with open('routes') as f:
        for line in f:
            if line.startswith('-----'):
                routes.append([])
                index += 1
            else:
                routes[index].append(line[:-1])
    return routes[:-1]

def set_waypoints(routes: list[list[str]]):
    print('Authing to EVE Online ESI')
    user_esi = esi.auth(client_id, client_secret, callback_url, scopes)
    index = -1
    while not (index >= 1 and index <= len(routes)):
        print(f'There is {len(routes)} set of routes')
        try:
            choice = input(f'Start with the route ({1} - {len(routes)}):')
            index = int(choice)
        except ValueError:
            choice = choice.upper()
            match choice:
                case 'Q':
                    return
                case _:
                    index = -1
    index = index - 1
    while index < len(routes):
        for drill in routes[index]:
            print(drill)
            drill_id = user_esi.search(drill, esi.Entity_type.STRUCTURE)[0]
            user_esi.set_waypoint(drill_id)
        index += 1
        if index == len(routes): break
        input(f'Press enter to start the route #{index+1}')

def manage_users():
    menu = 'Choose one of the following options:\n'
    menu = menu + '\t(A): Add a new user\n'
    menu = menu + '\t(D): Delete a user\n'
    menu = menu + '\t(L): List all the users\n'
    menu = menu + '\t(Q): Quit'
    choice = None
    while True:
        print(menu)
        choice = input('=>')
        choice = choice.upper()
        match choice:
            case 'A':
                pass
            case 'D':
                pass
            case 'L':
                users = load_users()
                if len(users) == 0:
                    print('No users saved')
                    continue
                _user = ''
                for user in users:
                    _user = _user + user.char_name + ','
                _user = _user[:-1]
                print(_user)
            case 'Q':
                return
            case _:
                pass

def load_users() -> list[esi.Gateway]:
    users = []
    return users

def main_menu():
    menu = 'Choose one of the following options:\n'
    menu = menu + '\t(C): Calculate new set of routes\n'
    menu = menu + '\t(U): Use the current set of routes\n'
    menu = menu + '\t(M): Manage the list of authed users\n'
    menu = menu + '\t(Q): Quit'
    choice = None
    while True:
        print(menu)
        choice = input('=>')
        choice = choice.upper()
        match choice:
            case 'C':
                build_routes(verbose=True)
            case 'U':
                routes = load_routes()
                users = load_users()
                set_waypoints(routes)
            case 'M':
                manage_users()
            case 'Q':
                sys.exit(0)
            case _:
                pass
if __name__ == '__main__':
    main_menu()
