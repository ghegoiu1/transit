from datetime import datetime
from datetime import timedelta
import math
import optparse
import os.path
import random
import sys
import transitfeed
import urllib

import googlemaps
import json
import time
import urllib2
import urlparse

def AddNoiseToLatLng(lat, lng):
    """Add up to 500m of error to each coordinate of lat, lng."""
    m_per_tenth_lat = Distance(lat, lng, lat + 0.1, lng)
    m_per_tenth_lng = Distance(lat, lng, lat, lng + 0.1)
    lat_per_100m = 1 / m_per_tenth_lat * 10
    lng_per_100m = 1 / m_per_tenth_lng * 10
    return (lat + (lat_per_100m * 5 * (random.random() * 2 - 1)),
           lng + (lng_per_100m * 5 * (random.random() * 2 - 1)))

def Distance(lat0, lng0, lat1, lng1):

    deg2rad = math.pi / 180.0
    lat0 = lat0 * deg2rad
    lng0 = lng0 * deg2rad
    lat1 = lat1 * deg2rad
    lng1 = lng1 * deg2rad
    dlng = lng1 - lng0
    dlat = lat1 - lat0
    a = math.sin(dlat*0.5)
    b = math.sin(dlng*0.5)
    a = a * a + math.cos(lat0) * math.cos(lat1) * b * b
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return 6367000.0 * c

def FormatLatLng(lat_lng):
    """Format a (lat, lng) tuple into a string for maps.google.com."""
    return "%0.6f,%0.6f" % lat_lng

def GetRandomDatetime():
    dt = datetime.today() + timedelta(seconds=32400)
    return dt.replace(second=0, microsecond=0)

def LatLngsToGoogleUrl(source, destination, dt):
    """Return a URL for routing between two (lat, lng) at a datetime."""
    params = {"origin": FormatLatLng(source),
            "destination": FormatLatLng(destination),
            "mode":"transit",
            "departure_time":str(dt),
            "alternatives":"true",
            "key":"AIzaSyCM_PBoHyV8WpYcVCbe7zz6cfvZuH8Hilk"}
    url = urlparse.urlunsplit(("https", "maps.googleapis.com", "/maps/api/directions/json",
                             urllib.urlencode(params), ""))
    return url
  
def GetRoutes(locations, departure_time, limit):
    json_responses = []
    query = 0
    urls = []
    for source, destination in zip(locations[0:limit], locations[1:limit + 1]):
        # print LatLngsToGoogleUrl(source, destination, departure_time)
        urls.append(LatLngsToGoogleUrl(source, destination, departure_time))
    
    # Check if limit is bigger than our number of urls
    limit = limit if limit < len(urls) else len(urls)

    for i in range(0, limit):
        try:
            # Get the API response.
            response = str(urllib2.urlopen(urls[i]).read())
            json_responses.append(response)
            continue
        except IOError:
            continue
    return json_responses

class RandomQueries:

    schedule = None
    locations = None
    
    def __init__(self, schedule):
        self.schedule = schedule
        self.GetRandomLocationsNearStops()
        

    def GetRandomLocationsNearStops(self):
      """Return a list of (lat, lng) tuples."""
      self.locations = []
      for s in self.schedule.GetStopList():
          if 'rich' in s.stop_name:
            self.locations.append(AddNoiseToLatLng(s.stop_lat, s.stop_lon))

    def GetJsonResponses(self, departure_time, limit):
        return GetRoutes(self.locations, departure_time, limit)


    
