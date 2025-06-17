# TurionSpace

## Directory:

**satellite_pass_predictions.py**: Loads all of the satellite passes, outputs a JSON file, and creates a Gantt chart (Parts 1 and 3 of the assignment). <br>
This file accepts custom TLE file input (Bonus 3):<br>
Run `satellite_pass_predictions.py --filename [file name to TLE data] --folder [folder to several TLE files]` <br>
Note that either the --filename OR --folder command can be used. If no filename is provided, it will default to the `noaa_satellites.tle` file.

**pass_predictions.json**: Example JSON output when the above file is run on the `noaa_satellites.tle` file. 

**diagram.pdf**: In my `satellite_pass_predictions.py`, I did not find any Skyfield documentation to calculate the elevation angle at a point in time. All I could receive was the *time* at which a satellite reached its max elevation. Using this time period, I calculated the position of the Ground Station and the Satellite and calculated the angle of elevation. This pdf is a diagram that explains my calculations.

