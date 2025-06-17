# TurionSpace

## Directory:

satellite_pass_predictions.py: Loads all of the satellite passes, outputs a JSON file, and creates a Gantt chart (Parts 1 and 3 of the assignment). <br>
This file accepts custom TLE file input (Bonus 3):<br>
Run `satellite_pass_predictions.py --filename [file name to TLE data] --folder [folder to several TLE files]` <br>
Note that either the --filename OR --folder command can be used. If no filename is provided, it will default to the `noaa_satellites.tle` file.
