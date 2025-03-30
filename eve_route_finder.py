import EVE_DAO.models as eve

if __name__ == '__main__':
    try:
        results = eve.get_systems(eve.Galaxy.NEW_EDEN, verbose=True)
        system_name = 'mai'
        results = eve.search_system(system_name)
        for result in results:
            print(f'{result}, {result.stargates}')
    except eve.SystemNameError:
        print(f'Can\'t find a system with the name {system_name}')
