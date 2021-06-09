import requests

ODS_SEARCH_URL = 'https://public.opendatasoft.com/api/records/1.0/search/'


class Location(object):
    def __init__(self, name, lat, lon):
        super().__init__()
        self.name = name
        self.lat = lat
        self.lon = lon

    def __repr__(self):
        return f'<Location name="{self.name}" lat="{self.lat}" lon="{self.lon}" />'


def zip_to_location(zipcode):
    params = {
        'dataset': 'georef-united-states-of-america-zc-point',
        'refine.zipcode': zipcode,
    }
    result = requests.get(ODS_SEARCH_URL, params=params).json()
    if result['nhits'] > 0:
        fields = result['records'][0]['fields']
        name = '%s, %s' % (fields['usps_city'], fields['ste_name'])
        return Location(name, fields['geo_point_2d'][0], fields['geo_point_2d'][1])



def lat_lon_to_location(lat, lon):
    params = {
        'dataset': 'georef-united-states-of-america-zc-point',
        'geofilter.distance': f'{lat},{lon},8000',
    }
    result = requests.get(ODS_SEARCH_URL, params=params).json()
    if result['nhits'] > 0:
        fields = result['records'][0]['fields']
        name = '%s, %s' % (fields['usps_city'], fields['ste_name'])
        return Location(name, fields['geo_point_2d'][0], fields['geo_point_2d'][1])
