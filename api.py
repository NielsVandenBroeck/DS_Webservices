from flask import Flask, request, send_file
from flask_restful import Resource, Api, abort
from flask_restful_swagger import swagger
import requests
from io import BytesIO
import argparse

COUNTRY_URL = 'https://restcountries.com/v3.1/'
WEATHER_URL = 'https://api.openweathermap.org/data/2.5/'
GRAPH_URL = 'https://quickchart.io//chart/'

API_KEY = None

Favorites = []

app = Flask(__name__)
api = swagger.docs(Api(app), apiVersion='0.1')

class Countries(Resource):
    @swagger.operation(
        notes='Returns the name of all countries in a given continent, if no continent is given, it returns all countries of the world.',
        parameters=[
            {
                'name': 'continent',
                'description': 'The continent of which the countries are requested, if none, all countries are returned.',
                'required': False,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'query'
            }
        ]
    )
    def get(self):
        continent = request.args.get('continent')
        # If no continent is given, retrieve all countries
        if continent is None:
            response = requests.get(f'{COUNTRY_URL}/all?fields=name')
        else:
            response = requests.get(f'{COUNTRY_URL}/region/{continent}?fields=name')
        # If the request went wrong in any way, return the error message
        if response.status_code != 200:
            abort(response.status_code)
        countries = response.json()
        # Add only the name of the countries to names
        names = []
        for item in countries:
            if 'name' not in item: continue
            if 'official' not in item['name']: continue
            names.append({'name': item['name']['official']})
        return names, 200


class Details(Resource):
    @swagger.operation(
        notes='Returns the latitude, longitude, capital city, population, size and area of a given country.',
        parameters=[
            {
                'name': 'country',
                'description': 'The country of which the details are requested.',
                'required': True,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'path'
            }
        ]
    )
    def get(self, country):
        response = requests.get(f'{COUNTRY_URL}/name/{country}?fullText=true')
        # If the request went wrong in any way, return the error message
        if response.status_code != 200:
            abort(response.status_code)
        # Put Data in json format
        info = response.json()[0]
        details = {
                'longitude': info['capitalInfo']['latlng'][1],
                'latitude': info['capitalInfo']['latlng'][0],
                'population': info['population'],
                'area': info['area']
            }
        return details, 200

class Temperature(Resource):
    @swagger.operation(
        notes='Returns the temperature of a given country.',
        parameters=[
            {
                'name': 'country',
                'description': 'The country of which the temperature is requested.',
                'required': True,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'path'
            }
        ]
    )
    def get(self, country):
        details = Details().get(country)
        lat = details[0]['latitude']
        lon = details[0]['longitude']
        response = requests.get(f'{WEATHER_URL}/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric')
        # If the request went wrong in any way, return the error message
        if response.status_code != 200:
            abort(response.status_code)
        # Return the current temperature of the country
        return {'temperature': response.json()['main']['temp']}, 200

class Favorite(Resource):
    @swagger.operation(
        notes='Adds a country to favorites',
        parameters=[
            {
                'name': 'country',
                'description': 'The country which is set to favorite.',
                'required': True,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'path'
            }
        ]
    )
    def post(self, country):
        response = requests.get(f'{COUNTRY_URL}/name/{country}?fullText=true')
        # If the request went wrong in any way, return the error message
        if response.status_code != 200:
            abort(response.status_code)
        name = response.json()[0]['name']['official']
        # Don't add if country is already present in list of favorites
        if name in Favorites:
            return {'message': f'{name} is already a favorite.'}, 200
        # Add to favorite list and return successful message
        Favorites.append(name)
        return {'message': f'{name} has been added to favorites.'}, 200

class Unfavorite(Resource):
    @swagger.operation(
        notes='Removes a country from favorites',
        parameters=[
            {
                'name': 'country',
                'description': 'The country which is deleted from favorites.',
                'required': True,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'path'
            }
        ]
    )
    def delete(self, country):
        response = requests.get(f'{COUNTRY_URL}/name/{country}?fullText=true')
        # If the request went wrong in any way, return the error message
        if response.status_code != 200:
            abort(response.status_code)
        name = response.json()[0]['name']['official']
        # Only remove if country is present in list of favorites
        if name in Favorites:
            Favorites.remove(name)
            return {'message': f'{name} has been removed from favorites.'}, 200
        return {'message': f'{name} was no favorite.'}, 200


class ListFavorites(Resource):
    @swagger.operation(
        notes='returns a list of all favorite countries'
    )
    def get(self):
        # Return the list of favorites in json format
        names = []
        for item in Favorites:
            names.append({"name": item})
        return names, 200

class TemperatureGraph(Resource):
    @swagger.operation(
        notes='Creates a graph with the temperature of a given country for the next n days',
        parameters=[
            {
                'name': 'country',
                'description': 'Country of which graph is requested.',
                'required': True,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'path'
            },
            {
                'name': 'n',
                'description': 'Number of coming days to measure temperature.',
                'required': True,
                'allowMultiple': False,
                'dataType': 'string',
                'paramType': 'query'
            }
        ]
    )
    def get(self, country):
        n = request.args.get('n')
        try:
            n = int(n)
        except:
            return {'message': f'the parameter n: {n} is not a number. Should be an integer between 1 and 5.'}, 400
        if n < 1 or n > 5:
            return {'message': f'the given amount of days {n} is invalid. Should be an integer between 1 and 5.'}, 400
        # Details needed for the request to the weather API
        details = Details().get(country)
        lat = details[0]['latitude']
        lon = details[0]['longitude']
        forecastResponse = requests.get(f'{WEATHER_URL}/forecast?lat={lat}&lon={lon}&appid={API_KEY}&cnt={n*8}&units=metric')
        # If the request went wrong in any way, return the error message
        if forecastResponse.status_code != 200:
            abort(forecastResponse.status_code)
        # Format and data for the request to the graph API
        timeslots = []
        temperatures = []
        for timeslot in forecastResponse.json()['list']:
            timeslots.append(timeslot['dt_txt'])
            temperatures.append(timeslot['main']['temp'])
        data = {
          'type': 'line',
          'data': {
            'labels': timeslots,
            'datasets': [
              {
                'label': f'Temperature Forecast in {country}',
                'data': temperatures,
                'fill': 'false',
              }
            ]
          }
        }

        chart_response = requests.get(f'{GRAPH_URL}/chart?c={data}')

        # If the request went wrong in any way, return the error message
        if chart_response.status_code != 200:
            abort(chart_response.status_code)

        image_bytes = chart_response.content
        return send_file(BytesIO(image_bytes), mimetype='image/png')

api.add_resource(Countries, '/countries')
api.add_resource(ListFavorites, '/favorites')
api.add_resource(Details, '/country/<country>/details')
api.add_resource(Temperature, '/country/<country>/temperature')
api.add_resource(Favorite, '/country/<country>/favorite')
api.add_resource(Unfavorite, '/country/<country>/unfavorite')
api.add_resource(TemperatureGraph, '/country/<country>/graph')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='API Web Service')
    parser.add_argument('--key', type=str, help='Weather API key needed for operation', required=True)
    args = parser.parse_args()
    API_KEY = args.key

    app.run()
