import requests
from PIL import Image
from io import BytesIO

# Base URL for the API - replace this with the actual URL where the API is hosted
API_BASE_URL = "http://localhost:5000"

def testAPI():
    print("Show all countries of Europe:")
    print(requests.get(f"{API_BASE_URL}/countries", params={'continent': "Europe"}).json())
    print("Retrieve details about Belgium:")
    print(requests.get(f"{API_BASE_URL}/country/Belgium/details").json())
    print("Retrieve temperature of Belgium:")
    print(requests.get(f"{API_BASE_URL}/country/Belgium/temperature").json())
    print("Make Belgium and Germany favorites, then print all favorites:")
    requests.post(f"{API_BASE_URL}/country/Belgium/favorite")
    requests.post(f"{API_BASE_URL}/country/Germany/favorite")
    print(requests.get(f"{API_BASE_URL}/favorites").json())
    print("Remove Germany from favorites, then print all favorites again:")
    requests.delete(f"{API_BASE_URL}/country/Germany/unfavorite")
    print(requests.get(f"{API_BASE_URL}/favorites").json())
    print("Show the forecast of the temperature in Belgium for the following 5 days:")
    graph = requests.get(f"{API_BASE_URL}/country/Belgium/graph", params={'n': 5})
    image_bytes = BytesIO(graph.content)
    image = Image.open(image_bytes)
    image.show()

def findWarmestCountry():
    print("Retrieve all countries of the continent South America:")
    south_american_countries = requests.get(f"{API_BASE_URL}/countries", params={'continent': "South America"}).json()
    print(south_american_countries)
    warmest_country = None
    highest_temperature = None

    for country in south_american_countries:
        name = country['name']
        current_temp = requests.get(f"{API_BASE_URL}/country/{name}/temperature").json()['temperature']
        print(f"Current temperature in {name}: {current_temp} degrees.")
        if current_temp is not None and (highest_temperature is None or current_temp > highest_temperature):
            warmest_country = name
            highest_temperature = current_temp

    if warmest_country:
        print(f"The warmest country in South America is currently {warmest_country}.")
        requests.post(f"{API_BASE_URL}/country/{warmest_country}/favorite")
        print(f"{warmest_country} has been added to favorites.")
        print(f"Showing graph of the temperature of {warmest_country} the next four days in a new window.")
        graph = requests.get(f"{API_BASE_URL}/country/{warmest_country}/graph", params={'n': 4})
        image_bytes = BytesIO(graph.content)
        image = Image.open(image_bytes)
        image.show()

if __name__ == "__main__":
    print("-------------------------")
    print("Test all API endpoints:\n")
    testAPI()
    print("-------------------------")
    print("Find warmest county in country in South America:\n")
    findWarmestCountry()
    print("-------------------------")
