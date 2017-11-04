
from __future__ import division
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
    
    number_of_changes = []
    time_total = []
    shortest_time_total = None
    chosen_route = None
    delays = []
    
    time_transit = 0
    time_walking = 0
    time_waiting = 0

    json_data = None
    departure_time =None
    delay = 180

    def __init__(self, json_data, departure_time, gmaps=None):
        self.json_data = clean_json(json_data)
        self.departure_time = departure_time
        if not gmaps:
            self.gmaps = googlemaps.Client(key='AIzaSyDEj_co9D-7Cg9PHItaZ9qAYp4RFP7msrI')
        else:
            self.gmaps = gmaps

    def get_alternatives(self):
        self.alternatives = len(self.json_data)

    def get_number_of_changes(self):
        self.number_of_changes = []
        for route in self.json_data:
            changes = 0
            for step in route['legs'][0]['steps']:
                if step['travel_mode']=='TRANSIT':
                    changes +=1
            self.number_of_changes.append(changes)
    
    def get_time_total(self):
        self.time_total = []
        for route in self.json_data:
            self.time_total.append((route['legs'][0]['arrival_time']['value'] - self.departure_time)/60)
        self.chosen_route = self.json_data[np.argmin(self.time_total)]
        self.shortest_time_total = (self.chosen_route['legs'][0]['arrival_time']['value'] - self.departure_time)/60

    def get_time_stats(self):
        time = 0
        for step in self.chosen_route['legs'][0]['steps']:
            if step['travel_mode']=='TRANSIT':
                self.time_transit += step['duration']['value']
            elif step['travel_mode']=='WALKING':
                self.time_walking += step['duration']['value']
        self.time_transit /=60
        self.time_walking /=60

    def get_waiting_time(self):
        current_time = self.chosen_route['legs'][0]['departure_time']['value']
        for step in self.chosen_route['legs'][0]['steps']:
            if step['travel_mode']=='WALKING':
                current_time += step['duration']['value']
            elif step['travel_mode']=='TRANSIT':
                self.time_waiting += step['transit_details']['departure_time']['value'] - current_time
                current_time = step['transit_details']['arrival_time']['value']
        self.time_waiting /=60 

    def get_general_stats(self):
        if len(self.json_data) > 0:
            self.get_alternatives()
            self.get_number_of_changes()
            self.get_time_total()
            self.get_time_stats()
            self.get_waiting_time()
            self.simulate_route_loss()
            resdict = {}
            resdict["alternatives"] = self.alternatives
            resdict["connections"] = self.number_of_changes
            resdict["time per route"] = self.time_total
            resdict["shortest route"] = self.shortest_time_total
            resdict["waiting time for shortest route"] = self.time_waiting
            resdict["transit time for shortest route"] = self.time_transit
            resdict["walking time for shortest route"] = self.time_walking
            resdict["delays caused by missing a connection"] = self.delays
            return resdict

    def simulate_step_loss(self, start_location, departure_time, end_location, delay):
        departure_time = departure_time + delay   
        directions = self.gmaps.directions(start_location, end_location, mode='transit', departure_time=departure_time)
        if 'arrival_time' in directions[0]['legs'][0].keys():
            return directions[0]['legs'][0]['steps'][0]['html_instructions'], directions[0]['legs'][0]['arrival_time']
        else:
            return directions[0]['legs'][0]['steps'][0]['html_instructions'], {'value':directions[0]['legs'][0]['duration']['value']+departure_time}

    def simulate_route_loss(self):
        self.delays = [] 
        steps = self.chosen_route['legs'][0]['steps']
        departure_time = self.chosen_route['legs'][0]['departure_time']['value']
        end_location = self.chosen_route['legs'][0]['end_location']
        for step_no, step in enumerate(steps):
            if step['travel_mode'] == 'TRANSIT':             
                instructions, time_spent = self.simulate_step_loss(step['start_location'], departure_time, end_location, self.delay)
                self.delays.append((time_spent['value'] - self.chosen_route['legs'][0]['arrival_time']['value'])/60)
            departure_time += step['duration']['value']

          
