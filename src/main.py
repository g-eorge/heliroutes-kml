import csv
import re
import simplekml
from simplekml import Style, Color
from geopy.point import Point

HELI_ROUTE_ICON = 'http://maps.google.com/mapfiles/kml/shapes/triangle.png'
VRP_ICON = 'http://maps.google.com/mapfiles/kml/shapes/target.png'
HELIROUTES_CHART = 'https://lh3.googleusercontent.com/d/19p8_5CVs8iAaWxvXxF9mBzOnO9PiyV5C' 

heli_route_point_style = Style()
heli_route_point_style.iconstyle.icon.href = HELI_ROUTE_ICON

heli_route_point_style_mandatory = Style()
heli_route_point_style_mandatory.iconstyle.icon.href = HELI_ROUTE_ICON
heli_route_point_style_mandatory.iconstyle.color = Color.darkblue

vrp_point_style = Style()
vrp_point_style.iconstyle.icon.href = VRP_ICON

def _load(path):
    with open(path, 'r') as f:
        data = f.readlines()
    return data

def _csv_to_jsonl(data):
    return csv.DictReader(data)

def _latlon_to_str(lat_or_lon):
    return f"{lat_or_lon['degrees']} {lat_or_lon['minutes']}m {lat_or_lon['decimal_seconds']}s {lat_or_lon['hemisphere']}"

def _parse_point(latlon):
    reg = r'([0-9]{2})([0-9]{2})([0-9]{2})(\.[0-9]+)?(N|S)\s+([0-9]{3})([0-9]{2})([0-9]{2})(\.[0-9]+)?(W|E)'
    matches = re.match(reg, latlon)
    lat = dict(degrees=matches.group(1),
                minutes=matches.group(2),
                decimal_seconds=f'{matches.group(3)}{str(matches.group(4) or "")}',
                hemisphere=matches.group(5))
    lon = dict(degrees=matches.group(6),
                minutes=matches.group(7),
                decimal_seconds=f'{matches.group(8)}{str(matches.group(9) or "")}',
                hemisphere=matches.group(10))
    return Point.from_string(f'{_latlon_to_str(lat)} {_latlon_to_str(lon)}')

def _route_points(data):
    new_data = []
    for point in data:
        point['Parsed Lat/Long'] = _parse_point(point["Lat/Long"])
        new_data.append(point)
    return new_data

def _organise_by_route(points):
    routes = dict()
    for point in points:
        route_points = routes.get(point['Route'], [])
        route_points.append(point)
        routes[point['Route']] = route_points
    return routes

def _create_routes(kml, routes):
    for name in routes:
        folder = kml.newfolder(name=name)
        for point in routes[name]:
            name = point['Point']
            (lat, lon, alt) = point['Parsed Lat/Long']
            pnt = folder.newpoint(name=name, coords=[(lon,lat,alt)], description=point['Description'])
            pnt.style = heli_route_point_style_mandatory if point['Mandatory Report'] == 'Y' else heli_route_point_style

def _vrps(data):
    new_data = []
    for point in data:
        lat = point["Latitude"]
        lon = point["Longitude"]
        point['Parsed Lat/Long'] = _parse_point(f'{lat} {lon}')
        new_data.append(point)
    return new_data

def _create_vrps(kml, vrps):
    folder = kml.newfolder(name="VRPs")
    for vrp in vrps:
        (lat, lon, alt) = vrp['Parsed Lat/Long']
        pnt = folder.newpoint(name=vrp['VRP name'], coords=[(lon,lat,alt)], description=vrp['ICAO'])
        pnt.style = vrp_point_style

def _add_route_chart(kml):
    chart = kml.newgroundoverlay(name='Heli Routes Chart')
    chart.icon.href = HELIROUTES_CHART
    chart.icon.viewboundscale = 0.75
    chart.color = "9cffffff"
    chart.latlonbox.north = 51.70265353572094
    chart.latlonbox.south = 51.24652902346208
    chart.latlonbox.east = 0.2315316672775933
    chart.latlonbox.west = -0.8342820108997584
    chart.latlonbox.rotation = -0.9836900234222412
    chart.lookat.latitude = 51.47304444444445
    chart.lookat.longitude = -0.2699
    chart.lookat.range = 84000

def main():
    points_path = '../data/route-points.csv'
    vrps_path = '../data/VRP_list_2023_01_26_CRC_7DC69A71.csv'

    points_data = _csv_to_jsonl(_load(points_path))
    vrps_data = _csv_to_jsonl(_load(vrps_path))

    kml = simplekml.Kml(open=1)
    all_points = _route_points(points_data)
    routes = _organise_by_route(all_points)
    vrps = _vrps(vrps_data)
    _add_route_chart(kml)
    _create_routes(kml, routes)
    _create_vrps(kml, vrps)
    kml.save('../data/London Heli-Routes.kml')

if __name__ == "__main__":
    main()
