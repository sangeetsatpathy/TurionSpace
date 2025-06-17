from skyfield.api import load

max_days = 7.0         # download again once 7 days old
name = 'noaa_stations.tle'  # custom filename, not 'gp.php'

url = 'https://www.celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle'

load.download(url, filename=name)