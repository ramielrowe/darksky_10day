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
        'dataset': 'us-zip-code-latitude-and-longitude',
        'q': zipcode,
    }
    result = requests.get(ODS_SEARCH_URL, params=params).json()
    if result['nhits'] > 0:
        fields = result['records'][0]['fields']
        name = '%s, %s' % (fields['city'], fields['state'])
        return Location(name, fields['latitude'], fields['longitude'])



def lat_lon_to_location(lat, lon):
    params = {
        'dataset': 'us-zip-code-latitude-and-longitude',
        'geofilter.distance': f'{lat},{lon},8000',
    }
    result = requests.get(ODS_SEARCH_URL, params=params).json()
    if result['nhits'] > 0:
        fields = result['records'][0]['fields']
        name = '%s, %s' % (fields['city'], fields['state'])
        return Location(name, fields['latitude'], fields['longitude'])
