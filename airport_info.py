from papirus import PapirusComposite
import requests
from random import randrange
import datetime as dt
from dateutil.parser import parse
from gpiozero import Button
from time import sleep
import pytz
import login_info

# Main layout variables
titleLine = 2
firstLine = 22
secondLine = 36
thirdLine = 51
fourthLine = 66
fifthLine = 81

firstCol = 2
secondCol = 75
thirdCol = 150
leftCol = 2
midCol = 125
rightCol = 150

titleText = 18
mainText = 16

# Buttons
button1 = Button(26)
button2 = Button(19)
button3 = Button(20)
button4 = Button(16)


# API Variables
token_url = "https://api.lufthansa.com/v1/oauth/token"
token_auth = {
  "client_id":"",
  "client_secret":"",
  "grant_type":"client_credentials"
}
if login_info.token_auth:
  token_auth = login_info.token_auth
  
token = ""
params = {
  'serviceType':'passenger',
  'limit':'5'
}

code_params = {
  'lang':"en"
}

# API URLs
code_url = ""
flights_url = "https://api.lufthansa.com/v1/operations/flightstatus/departures/"
carrier_codes_url = "https://api.lufthansa.com/v1/mds-references/airlines/"
airport_codes_url = "https://api.lufthansa.com/v1/mds-references/airports/"


# Determines which airports the flights will be chosen from
codesArr = ["FRA","CDG","EWR","EDI","VIE","MUC","JFK","SEA","ORD","PHL","NCE","STR","ZRH","BSL","GLA"]

airport_codes = {
  "FRA":"Frankfurt Am Main",
  "CDG":"Charles de Gaulle",
  "EWR":"Newark Liberty",
  "VIE":"Vienna",
  "MUC":"Munich",
  "CPH":"Copenhagen Kastrup",
  "EDI":"Edinburgh"
}


status_codes = {
  "FE":  "Early",
  "NI":  "",
  "OT":  "On Time",
  "DL":  "Delayed",
  "NO":  "",
}



token = ""
headers = {}

def getToken():
  """
  Fetches an auth token from the api
  """
  global token
  global headers
  token_request = requests.post(token_url, data=token_auth)
  token = token_request.json()["access_token"]
  headers = {
    "Accept": "application/json",
    "Authorization": "Bearer " + token
  }

random_code = ""
depart_airport_tz = ""
depart_airport_name = ""
random_flight = {}
local_time = dt.datetime.now()


def getRandomAirport():
  """
  docstring
  """
  global random_code
  global depart_airport_tz
  global depart_airport_name
  global random_flight
  global local_time
  random_code = codesArr[randrange(codesArr.__len__())]
  print(random_code)
  # Get departure airport info (specifically to get timezone offset)
  depart_airport_request = requests.get(airport_codes_url+random_code , headers=headers, params=code_params)
  # returned data from api
  depart_airport_data = depart_airport_request.json()
  # check to see if the data has an array of airports or not and get the data appropriately
  if type(depart_airport_data["AirportResource"]["Airports"]["Airport"]) is list: 
    depart_airport_tz = depart_airport_data["AirportResource"]["Airports"]["Airport"][0]["TimeZoneId"]
    depart_airport_name = depart_airport_data["AirportResource"]["Airports"]["Airport"][0]["Names"]["Name"]["$"]
  else:
    depart_airport_tz = depart_airport_data["AirportResource"]["Airports"]["Airport"]["TimeZoneId"]
    depart_airport_name = depart_airport_data["AirportResource"]["Airports"]["Airport"]["Names"]["Name"]["$"]

  # get the current time with utc time
  now = dt.datetime.now(tz=dt.timezone.utc)
  # get the local timezone info for the departure airport
  timezone = pytz.timezone(depart_airport_tz)
  # convert the current utc time to local time at the airport
  local_time = now.astimezone(timezone)
  # make a string out of the local time to insert into the api url
  now_str = local_time.strftime("%Y-%m-%dT%H:%M")
  # trigger 
  flights_request = requests.get(flights_url+random_code+'/'+now_str , headers=headers, params=params)
  if flights_request.status_code == requests.codes.ok:
    print("Flight Found")
    flights_data = flights_request.json()
    flights_array = flights_data['FlightStatusResource']['Flights']['Flight']
    random_flight = flights_array[randrange(flights_array.__len__())]
  else:
    print("Flight Error")
    getRandomAirport()


while True:
  getToken()
  # Choose one of the airports to get flights from
  getRandomAirport()
  # Airline Info
  carrier_code = random_flight["OperatingCarrier"]["AirlineID"]
  carrier_request = requests.get(carrier_codes_url+carrier_code , headers=headers)
  carrier_data = carrier_request.json()
  airline = carrier_data["AirlineResource"]["Airlines"]["Airline"]["Names"]["Name"]["$"]

  # Airport Info
  

  dest_code = random_flight["Arrival"]["AirportCode"]
  print(dest_code)
  dest_airport_request = requests.get(airport_codes_url+dest_code , headers=headers, params=code_params)
  dest_airport_data = dest_airport_request.json()
  # check to see if it's an array or not. sometimes not an array
  if type(dest_airport_data["AirportResource"]["Airports"]["Airport"]) is list: 
    dest_airport_name = dest_airport_data["AirportResource"]["Airports"]["Airport"][0]["Names"]["Name"]["$"]
  else:
    dest_airport_name = dest_airport_data["AirportResource"]["Airports"]["Airport"]["Names"]["Name"]["$"]

  flight_num = random_flight["OperatingCarrier"]["FlightNumber"]

  # Departure Info
  dept_time_obj = parse(random_flight["Departure"]["ScheduledTimeUTC"]["DateTime"])
  timezone = pytz.timezone(depart_airport_tz)
  dept_time_str = dept_time_obj.astimezone(timezone).strftime("%H:%M")
  flight_status = random_flight["Departure"]["TimeStatus"]["Code"]
  flight_status_formatted = status_codes[flight_status]

  terminal_info = random_flight["Departure"]["Terminal"] if "Terminal" in random_flight["Departure"] else {}

  gate = " G:"+ terminal_info["Gate"] if "Gate" in terminal_info else ""
  terminal_name = "T:" + terminal_info["Name"] if "Name" in terminal_info else ""
  terminal = terminal_name+" "+ gate

  # Arrival Info
  arrival_time_obj = parse(random_flight["Arrival"]["ScheduledTimeUTC"]["DateTime"])
  arrival_time_str = arrival_time_obj.strftime("%H:%M")
  flight_length_arr = str(arrival_time_obj - dept_time_obj).split(":")
  flight_length_hours = flight_length_arr[0] if len(flight_length_arr[0]) > 1 else "0"+flight_length_arr[0]
  flight_length = flight_length_hours + ":" + flight_length_arr[1]

  local_time_str = local_time.strftime("%H:%M")


  # initiate screen info
  textNImg = PapirusComposite(False, rotation = 0)

  # Add base background image
  textNImg.AddImg("./display-background2.png",0,0,(200,96), Id="background")

  # formatting for display
  airline_name = airline[:10] if len(airline) > 10 else airline

  depart_airport_name_formatted = depart_airport_name[:17] if len(depart_airport_name) > 17 else depart_airport_name
  dest_airport_name_formatted = dest_airport_name[:17] if len(dest_airport_name) > 17 else dest_airport_name


  # Title Line
  textNImg.AddText(airline_name, leftCol, titleLine,titleText, Id="Carrier" , invert=True)
  textNImg.AddText(flight_num, rightCol, titleLine,titleText, Id="Flight" , invert=True)
  # First Line
  textNImg.AddText("D:" + depart_airport_name_formatted, firstCol, firstLine,mainText, Id="departAirport")
  # Second Line
  textNImg.AddText("A:"+ dest_airport_name_formatted, firstCol, secondLine, mainText, Id="arriveAirport")
  # Third Line
  textNImg.AddText(terminal, firstCol, thirdLine,mainText, Id="terminal")
  textNImg.AddText(flight_status_formatted, midCol, thirdLine,mainText, Id="status")
  # Fourth Line
  textNImg.AddText("Depart", firstCol, fourthLine,mainText, Id="depart")
  textNImg.AddText("Length", secondCol, fourthLine,mainText, Id="length")
  textNImg.AddText("Time", thirdCol, fourthLine,mainText, Id="time")
  # Fifth Line
  textNImg.AddText(dept_time_str, firstCol, fifthLine,mainText, Id="deptTime")
  textNImg.AddText(flight_length, secondCol, fifthLine,mainText, Id="flightLen")
  textNImg.AddText(local_time_str, thirdCol, fifthLine,mainText, Id="localTime")

  textNImg.WriteAll()
  sleep(120)