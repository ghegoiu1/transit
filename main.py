import simplejson as json
from infoextract import InfoExtract


if __name__ == "__main__":
    with open('route.json') as route_path:
        route_data = json.load(route_path)
    departure_time = 1509007000
    extract = InfoExtract(route_data, departure_time)
    
    print extract.get_time_total()
    extract.simulate_route_loss()

