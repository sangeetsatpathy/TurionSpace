from skyfield.api import load
from skyfield.iokit import parse_tle_file
from skyfield.api import wgs84
from skyfield.trigonometry import position_angle_of
import numpy as np
import math
import json
import argparse
import os
import datetime
import pandas as pd
import plotly.figure_factory as ff

#Calculates the angle of elevation of the satellite.
def calculate_satellite_angle(location, satellite, time):
    geocentric_pos_station = np.array(location.at(time).xyz.km)
    relative_satellite_pos = np.array((satellite - location).at(time).xyz.km) #calculate the satellite position vector FROM station
    # this works because both the GeographicPosition class and the EarthSatellite class inherit from VectorFunction.

    #calculate the projection of the satellite's relative vector onto the ground-station's geocentric vector.
    scalar_mult = np.dot(relative_satellite_pos, geocentric_pos_station) / np.dot(geocentric_pos_station, geocentric_pos_station)
    projected_vector = scalar_mult * geocentric_pos_station

    planar_vector = relative_satellite_pos - projected_vector
    planar_distance = math.sqrt(np.dot(planar_vector, planar_vector))
    vertical_distance = math.sqrt(np.dot(projected_vector, projected_vector))

    theta = math.atan(vertical_distance / planar_distance)
    return theta

def generate_timeline_plot(master_list):
    graph_list = []
    for sat_pass in master_list:
        graph_list.append(dict(Task=sat_pass["satellite_name"], Start=sat_pass["start_time"], Finish=sat_pass["end_time"]))
    fig = ff.create_gantt(graph_list, group_tasks=True)
    fig.show()

class Satellite:
    def __init__(self, name):
        self.name = name
        self.passes = []
    
    #When adding passes, add so it is sorted by the start times.
    def add_pass(self, satellite_pass):
        if len(self.passes) == 0:
            self.passes.append(satellite_pass)
            return
        i = 0
        while(i<len(self.passes) and satellite_pass.get_start_time() > self.passes[i].get_start_time()): 
            i+=1
        
        if(i == len(self.passes)):
            self.passes.append(satellite_pass)
        else:
            self.passes.insert(i, satellite_pass)

    def generate_statistics(self):
        print(f"Satellite Name: {self.name}")
        print(f"Total number of passes: {len(self.passes)}.")
        avg_time_between_passes, total_contact_time = self.calculate_stats()

        print(f"Average time between passes (in minutes): {avg_time_between_passes * 1440}. Total contact time for satellite (in minutes): {total_contact_time * 1440}")
        print("--------")
        print("Pass Details:")
        json_list = []
        for sat_pass in self.passes:
            print(f"Start time: {sat_pass.get_start_time().utc_datetime()}. End time: {sat_pass.get_end_time().utc_datetime()}. Duration (in minutes): {sat_pass.get_duration() * 1440}. Maximum elevation angle reached: {sat_pass.get_max_elevation()}. Ground station coordinates: {sat_pass.get_ground_station()}.")
            current_dict = {
                "satellite_name":sat_pass.get_satellite(),
                "ground_station":sat_pass.get_ground_station(),
                "start_time":sat_pass.get_start_time().utc_datetime(),
                "end_time":sat_pass.get_end_time().utc_datetime(),
                "duration_minutes":sat_pass.get_duration() * 1440,
                "max_elevation":sat_pass.get_max_elevation()
            }
            json_list.append(current_dict)
        print("================")
        return json_list
    
    def calculate_stats(self):
        sum_between_passes = 0
        sum_contact_time = 0
        for i in range(len(self.passes) - 1):
            difference = self.passes[i + 1].get_start_time() - self.passes[i].get_end_time() #We know that the passes are sorted by start_time already.
            contact_time = self.passes[i].get_duration()
            if difference < 0:
                contact_time -= difference #This offsets possible double-counting of total exposure time if there is an overlap between time schedules
                difference = 0
            sum_between_passes += difference
            sum_contact_time += contact_time
        
        average_time_between_passes = sum_between_passes / (len(self.passes) - 1)
        return average_time_between_passes, sum_contact_time

class Pass:
    def __init__(self, satellite_name, gnd_location, start_time, end_time, max_elev):
        self.satellite = satellite_name
        self.ground_station = gnd_location
        self.start_time = start_time
        self.end_time = end_time
        self.max_elevation = max_elev

    def get_ground_station(self):
        return f"Latitude: {self.ground_station.latitude}. Longitude: {self.ground_station.longitude}"
    
    def get_start_time(self):
        return self.start_time
    
    def get_end_time(self):
        return self.end_time

    def get_max_elevation(self):
        return self.max_elevation

    #Note: the duration is outputted in days
    def get_duration(self):
        duration = self.end_time - self.start_time
        return duration
    
    def get_satellite(self):
        return self.satellite


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename")
    parser.add_argument("--folder")
    args, leftovers = parser.parse_known_args()
    filename = 'noaa_satellites.tle'
    use_folder = False
    if args.filename is not None and os.path.exists(args.filename):
        filename = args.filename
    elif args.folder is not None and os.path.exists(args.folder):
        use_folder = True
    

    ts = load.timescale()
    t_0 = ts.now()
    t_f = t_0 + 7 # 7 days later.
    
    satellites = []
    if use_folder:
        for entry in os.scandir(directory):  
            if entry.is_file():  # check if it's a file
                with load.open(entry) as f:
                    satellites.extend(list(parse_tle_file(f, ts)))
    else:
        with load.open(filename) as f:
            satellites = list(parse_tle_file(f, ts))

    # by now, we have a list of EarthSatellites
    sf = wgs84.latlon(+37.7743,-122.4683)
    bluffton = wgs84.latlon(+40.8939, -83.8917)
    beijing = wgs84.latlon(+40.1906,+116.4121)

    list_locations = [sf, bluffton, beijing]

    satellite_objects = []

    for sat in satellites:
        curr_sattelite = Satellite(sat.name)
        for loc in list_locations:
            t, events = sat.find_events(loc, t_0, t_f, altitude_degrees=10.0)
            
            current_start_time = t_0
            current_end_time = t_0
            previous_highest_angle = 10.0
            for (time, event) in zip(t, events):
                if event == 0: #if the satellite has just entered into the visible zone
                    current_start_time = time

                elif event == 1: # if the satellite has 'culminated' (a max angle)
                    angle = calculate_satellite_angle(loc, sat, time) * (180 / math.pi)
                    if angle > previous_highest_angle:
                        previous_highest_angle = angle

                else: # if the satellite has exited the visible zone
                    current_end_time = time
                    curr_sattelite.add_pass(Pass(sat.name, loc, current_start_time, current_end_time, previous_highest_angle)) #add a new Pass object

                    # reset the variables to get ready for the next pass
                    previous_highest_angle = 10.0
                    current_start_time = t_0
                    current_end_time = t_0
        satellite_objects.append(curr_sattelite)

    master_list = []
    for satellite_obj in satellite_objects:
        master_list.extend(satellite_obj.generate_statistics()) # adds all of the Passes in the current satellite into the master list
    generate_timeline_plot(master_list)
    json_object = json.dumps(master_list, indent=4, default=str)

    with open("pass_predictions.json", "w") as outfile:
        outfile.write(json_object)