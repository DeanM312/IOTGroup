import requests, json, time

class TempAPI:
    apiKey = 'a8601a0a968e4770fc76fb73440e2d39'

    def __init__(self):
        pass

    def getTemp(self):
        req = 'https://api.openweathermap.org/data/2.5/weather?lat=-37.8142176&lon=144.9631608&appid=a8601a0a968e4770fc76fb73440e2d39'
    
        resp = requests.get(req)
        jsonResp = json.loads(resp.text)

        return '{:.2f}'.format(jsonResp['main']['temp'] - 273.15)

if __name__ == '__main__':
    api = TempAPI()
    print(api.getTemp())
