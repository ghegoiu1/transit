import simplejson as json
import numpy as np
import googlemaps
import datetime

def clean_json(json_data):
    routes = [] 
    for route in json.loads(json_data)['routes']:
        if 'arrival_time' in route['legs'][0].keys():
            routes.append(route)
    return routes

class InfoExtract:

    alternatives = None
    
    mean_number_of_changes = None
    mean_time_total = None
    shortest_time_total = None
    chosen_route = None
    
    time_transit = 0
    time_walking = 0
    time_waiting = 0

    json_data = None
    departure_time =None
    delay = 1000

    def __init__(self, json_data, departure_time, gmaps=None):
        self.json_data = clean_json(json_data)
        self.departure_time = departure_time
        if not gmaps:
            self.gmaps = googlemaps.Client(key='AIzaSyDEj_co9D-7Cg9PHItaZ9qAYp4RFP7msrI')
        else:
            self.gmaps = gmaps

    def get_alternatives(self):
        self.alternatives = len(self.json_data)
        return self.alternatives

    def get_number_of_changes(self):
        no_changes = []
        
        for route in self.json_data:
            changes = 0
            for step in route['legs'][0]['steps']:
                if step['travel_mode']=='TRANSIT':
                    changes +=1
            no_changes.append(changes)
        self.mean_number_of_changes = np.mean(no_changes)
        return self.mean_number_of_changes
    
    def get_time_total(self):
        times = []
        for route in self.json_data:
            times.append(route['legs'][0]['arrival_time']['value'] - self.departure_time)
        self.mean_time_total = np.mean(times)
        self.chosen_route = self.json_data[np.argmin(times)]
        self.shortest_time_total = self.chosen_route['legs'][0]['arrival_time']['value'] - self.departure_time
        return self.mean_time_total, self.shortest_time_total

    def get_time_stats(self):
        time = 0
        for step in self.chosen_route['legs'][0]['steps']:
            if step['travel_mode']=='TRANSIT':
                self.time_transit += step['duration']['value']
            elif step['travel_mode']=='WALKING':
                self.time_walking += step['duration']['value']
        return self.time_transit, self.time_walking

    def get_waiting_time(self):
        current_time = self.chosen_route['legs'][0]['departure_time']['value']
        for step in self.chosen_route['legs'][0]['steps']:
            if step['travel_mode']=='WALKING':
                current_time += step['duration']['value']
            elif step['travel_mode']=='TRANSIT':
                self.time_waiting += step['transit_details']['departure_time']['value'] - current_time
                current_time = step['transit_details']['arrival_time']['value']
        return self.time_waiting

    def get_general_stats(self):
        if len(self.json_data) > 0:
            resdict = {}
            resdict["alternatives"] = self.get_alternatives()
            resdict["connections"] = self.get_number_of_changes()
            self.get_time_total()
            resdict["mean time"] = self.mean_time_total
            resdict["shortest time"] = self.shortest_time_total
            resdict["waiting time"] = self.get_waiting_time()
            self.get_time_stats()
            resdict["transit time"] = self.time_transit
            resdict["walking time"] = self.time_walking
            return resdict

    def simulate_step_loss(self, start_location, departure_time, end_location, delay):
        departure_time = departure_time + delay   
        directions = self.gmaps.directions(start_location, end_location, mode='transit', departure_time=departure_time)
        return directions[0]['legs'][0]['steps'][0]['html_instructions'], directions[0]['legs'][0]['arrival_time']

    def simulate_route_loss(self):
        steps = self.chosen_route['legs'][0]['steps']
        departure_time = self.chosen_route['legs'][0]['departure_time']['value']
        end_location = self.chosen_route['legs'][0]['end_location']
        for step_no, step in enumerate(steps):
            print step['travel_mode']


            if step['travel_mode'] == 'TRANSIT':
                print 'Transit step lost'
                print step['html_instructions']
                print 'Transit departure time {}'.format(datetime.datetime.fromtimestamp(step['transit_details']['departure_time']['value']))
                
                print
                print 'Our time {}'.format(datetime.datetime.fromtimestamp(departure_time + self.delay))
                instructions, time_spent = self.simulate_step_loss(step['start_location'], departure_time, end_location, self.delay)
                print instructions
                print 'New arrival time {}'.format(time_spent)
                print
            departure_time += step['duration']['value']

          
