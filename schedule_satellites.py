import numpy as np
import math
import json
import argparse
import os
import datetime
from satellite_pass_prediction import Pass, Satellite

class GroundStation:
    def __init__(self, location):
        self.loc = location
        self.pass_schedule = []

class Satellite:
    def __init__(self, name):
        self.name = name
        self.potential_passes = []
        self.current_total_min = 0 

    #Passes are already sorted based on start_time; from JSON file (within each satellite)
    def add_pass(self, new_pass):
        self.potential_passes.append(new_pass)

    def get_passes(self):
        return self.potential_passes

    #Only used by GroundStation
    def get_current_total_minutes(self):
        return self.current_total_min
    
    def add_total_minutes(self, minutes):
        self.current_total_min += minutes

class Pass:
    def __init__(self, satellite_name, gnd_location, start_time, end_time):
        self.satellite = satellite_name
        self.ground_station = gnd_location
        self.start_time = start_time
        self.end_time = end_time

    def get_ground_station(self):
        return f"Latitude: {self.ground_station.latitude}. Longitude: {self.ground_station.longitude}"
    
    def get_start_time(self):
        return self.start_time
    
    def get_end_time(self):
        return self.end_time

    def set_start_time(self, new_start_time):
        self.start_time = new_start_time
    
    def set_end_time(self, new_end_time):
        self.end_time = new_end_time

    #Note: the duration is outputted in days
    def get_duration(self):
        duration = self.end_time - self.start_time
        return duration
    
    def get_satellite(self):
        return self.satellite

class CentralizedGroundControl:
    def __init__(self):
        self.list_of_passes = []
        self.satellites_dict = {}
    
    # Inserts the pass object sorted based on the start time.
    def insert_pass(self, pass_object):
        #Pre-processing the Pass to create Satellite objects; this will be useful in checking whether a Satellite can offload onto another ground station.
        satellite_name = pass_object.get_satellite()
        if satellite_name not in self.satellites_dict:
            self.satellites_dict.update({satellite_name:Satellite(satellite_name)})

        # Inserts the pass into the central ground station control.
        if len(self.list_of_passes) == 0:
            self.list_of_passes.append(pass_object)
            return
        i = 0
        while(i<len(self.list_of_passes) and pass_object.get_start_time() > self.passes[i].get_start_time()):
            i+=1
        
        if(i == len(self.list_of_passes)):
            self.passes.append(pass_object)
        else:
            self.passes.insert(i, pass_object)

    ## This is INCOMPLETE. There are too many cases to check in scheduling, considering multiple ground locations;
    def process_passes(self):
        while i <= len(self.list_of_passes) - 1:
            k = i
            current_pass = self.list_of_passes[i]
            end_time_curr = current_pass.get_end_time()
            curr_satellite_name = current_pass.get_satellite()
            list_interferences = []
            potential_offloads = []
            while k <= len(self.list_of_passes) - 1 and self.list_of_passes[k].get_start_time() < end_time_curr:
                if self.list_of_passes[k].get_ground_station() == current_pass.get_ground_station():
                    #The satellites are conflicting.
                    list_interferences.append(self.list_of_passes[k])
                else:
                    #Note: if there is a space block in another ground station: if the block started before this 
                    potential_offloads.append(self.list_of_passes[k])

            #KEY ASSUMPTION: passes are never fully overlapped over each other.
            conflicted_start_time = list_interferences[0].get_start_time()
            conflicted_end_time = current_pass.get_end_time()
                

            #check if any of the sattelites can be offloaded onto another ground station
                    
            # Update the total values of each satellite (for priority)

            #After scheduling any Pass and adding it to that GroundStation. 
            #Then "push forward" the start_times for all non-scheduled, overlapping passes of the same satellite in different ground stations. The Satellite is not free. 

            i+=1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename")
    args, leftovers = parser.parse_known_args()
    filename = 'pass_predictions.json'
    use_folder = False
    if args.filename is not None and os.path.exists(args.filename):
        filename = args.filename
    
    with open(filename, 'r') as input_file:
        data = json.load(input_file)

    set_of_stations = {}
    arr_gnd_stations = []

    gnd_control = CentralizedGroundControl()
    for entry in data:
        sat_name = entry["satellite_name"]
        gnd_station = entry["ground_station"]
        if gnd_station not in set_of_stations:
            set_of_stations.add(gnd_station)
            arr_gnd_stations.append(GroundStation(gnd_station))
        start_time = datetime.strptime(entry["start_time"], "%Y-%m-%d %H:%M:%S.%f%z")
        end_time = datetime.strptime(entry["end_time"], "%Y-%m-%d %H:%M:%S.%f%z")
        gnd_control.insert_pass(Pass(sat_name, gnd_station, start_time, end_time))

    
    
    # Now all of the passes have been added to the Centralized Ground Scheduling System.
    # We now iterate through the passes, checking if there are interferences
    # Possibilities (not mutually exclusive):
    #   a) Overlapping, 2 satellites same station
    #   b) Overlapping, same satellite, 2 stations
    # If a second satellite makes a request to join while a first satellite is active, we should first check if either of them can be handed off to another station without interfering.
    # If the other stations are full, or neither of the satellites are within range of another station, then we prioritize the one with less equal pass times

    # When there are interferences on the SAME STATION, we should single out the 'overlapping' time period and make it an individual Pass which is "conflicted". 
    # Then, keep searching the array for time periods that start after the 'overlapping' start, and stop checking once you find a pass that starts after the 'end' of the overlap.
    # This search is to find time periods in which that satellite could go to another ground station.

    # So how do we store the results? Each ground station should have a finalized schedule of Passes.
    gnd_control.process_passes()
