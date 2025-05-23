#! /usr/bin/env python3
from papirus import PapirusComposite
import requests
from random import randrange
import datetime as dt
from dateutil.parser import parse
from gpiozero import Button
from time import sleep
import pytz
import login_info
import codes

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
midCol = 129
rightCol = 155

titleText = 18
mainText = 16

# Buttons
button1 = Button(26)
button2 = Button(19)
button3 = Button(20)
button4 = Button(16)

# reuse token for more than one call at a time
# try to figure out why it's refreshing the screen 3-4 times each cycle




# API Variables
token_url = "https://api.lufthansa.com/v1/oauth/token"
token_auth = {"client_id": "", "client_secret": "", "grant_type": "client_credentials"}
if login_info.token_auth:
    token_auth = login_info.token_auth

token = ""
params = {"serviceType": "passenger", "limit": "10"}
code_params = {"lang": "en"}

# API URLs
code_url = ""
flights_url = "https://api.lufthansa.com/v1/operations/flightstatus/departures/"
# carrier_codes_url = "https://api.lufthansa.com/v1/mds-references/airlines/"
airport_codes_url = "https://api.lufthansa.com/v1/mds-references/airports/"


# Determines which airports the flights will be chosen from
    # "FRA", # Frankfurt - gives an error when testing out the API for some reason
codesArr = [
    "CDG", # Paris
    "EWR", # Newark
    "EDI", # Edinburgh
    "VIE", # Vienna
    "MUC", # Munich
    "JFK", # JFK
    "SEA", # Seattle
    "ORD", # Chicago
    "PHL", # Philadelphia
    "NCE", # Nice
    "STR", # Strasbourg
    "ZRH", # Zurich
    "BSL", # Basel
    "GLA", # Glasgow
    "DUB", # Dublin
]


random_code = ""
depart_airport_tz = ""
depart_airport_name = ""
random_flight = {}
local_time = dt.datetime.now()
token = ""
token_expire_time = dt.datetime.now()

# token_expire_time = int(dt.datetime.now().timestamp())
headers = {}
last_airport_code = ""
textNImg = PapirusComposite(False)
# textNImg = PapirusComposite(False, rotation=180) # This flips the readout 180 degrees
# textNImg = PapirusComposite() # This puts up info without needing the .WriteAll() function
textNImg.AddText("Initializing", Id="Start")
textNImg.WriteAll()

textNImg.AddImg(
    "/home/pi/rpi-epaper-airport/display-background2.png",
    0,
    0,
    (200, 96),
    Id="background",
)
# textNImg.WriteAll()


def getToken():
    """
  Fetches an auth token from the api
  """
    global token
    global token_expire_time
    global headers
    # set time to check as 1min before token should expire
    textNImg.UpdateText("Start", "Checking token ")
    textNImg.WriteAll()
    
    textNImg.UpdateText("Start", str(token_expire_time))
    textNImg.WriteAll()
    textNImg.UpdateText("Start", token_expire_time.timestamp())
    textNImg.WriteAll()
    temp_expire_time = token_expire_time - 60
    textNImg.UpdateText("Start", temp_expire_time)
    textNImg.WriteAll()
    textNImg.UpdateText("Start", int(dt.datetime.now().timestamp()))
    textNImg.WriteAll()
    textNImg.UpdateText("Start", int(dt.datetime.now().timestamp()) > temp_expire_time)
    textNImg.WriteAll()
    # if the current time is not before the expiration time, get a new token
    # otherwise, just keep using the current token
    # since the expiration time initializes as the current time it should always
    # force a token on the first try
    if dt.datetime.now() > temp_expire_time or token == "":
      textNImg.UpdateText("Start", "Fetching token")
      textNImg.WriteAll()
      try:
        token_request = requests.post(token_url, data=token_auth)
        if token_request.status_code == requests.codes.ok:
            token_data = token_request.json()
            token = token_data["access_token"]
            textNImg.UpdateText("Start", "Token expires in: " + str(token_data["expires_in"]))
            textNImg.WriteAll()
            token_expire_time = dt.datetime.now() + dt.timedelta(seconds=int(token_data["expires_in"]))

            headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
            textNImg.UpdateText("Start", "Token expires at: " + token_expire_time)
            textNImg.WriteAll()
      except:
        # show error, wait, return
        
        textNImg.UpdateText("Start", "Token error.")
        textNImg.WriteAll()
        getToken()
        return
    return

def generateRandomAirportCode():
    global random_code
    global last_airport_code
    temp_code = codesArr[randrange(codesArr.__len__())]
    if temp_code != last_airport_code:
        random_code = temp_code
        last_airport_code = temp_code
    else:
        generateRandomAirportCode()


def getRandomAirport():
    """
  docstring
  """
    global random_code
    global depart_airport_tz
    global depart_airport_name
    global random_flight
    global local_time

    generateRandomAirportCode()

    depart_airport_name = codes.airport_codes_names[random_code]
    depart_airport_tz = codes.codes_timezone_offset[random_code]
   
    # get the current time with utc time
    now = dt.datetime.now(tz=dt.timezone.utc)
    # get the local timezone info for the departure airport
    timezone = pytz.timezone(depart_airport_tz)
    # convert the current utc time to local time at the airport
    local_time = now.astimezone(timezone)
    # make a string out of the local time to insert into the api url
    now_str = local_time.strftime("%Y-%m-%dT%H:%M")
    # trigger
    flights_request = requests.get(
        flights_url + random_code + "/" + now_str, headers=headers, params=params
    )
    # api call successful
    if flights_request.status_code == requests.codes.ok:
        flights_data = flights_request.json()
        # sometimes the api returns an array, sometimes a single item
        if type(flights_data["FlightStatusResource"]["Flights"]["Flight"]) is list:
            # get the array of flights
            flights_array = flights_data["FlightStatusResource"]["Flights"]["Flight"]
            random_flight_found = False
            # loop for checking through flights for airlines i want to ignore
            while random_flight_found is False:
              # each loop removes an item from the array so first check that the array has anything
              if len(flights_array) != 0:
                  # choose a random item from the array
                  random_index = randrange(flights_array.__len__())
                  temp_flight = flights_array[random_index]
                  # verify that flight isn't in the list of airlines to ignore
                  if temp_flight["MarketingCarrier"]["AirlineID"] not in codes.ignore_carrier_codes:
                      # use the flight
                      random_flight = temp_flight
                      # cancel out of loop
                      random_flight_found = True
                  else:
                      # if it's in the list, remove it from the array
                      flights_array.pop(random_index)
              else:
                  # not sure, but this could lead to a infinite loop so adding this to try to avoid that
                  random_flight_found = True
                  # nothing left in array so look for another flight
                  getRandomAirport()

        else:
            if temp_flight["MarketingCarrier"]["AirlineID"] not in codes.ignore_carrier_codes:
                random_flight = flights_data["FlightStatusResource"]["Flights"]["Flight"]
            else:
                getRandomAirport()

    else:
        textNImg.UpdateText("Start", "Flight error")
        textNImg.WriteAll()
        getRandomAirport()



def displayFlightInfo():
    getToken()
    # Choose one of the airports to get flights from
    getRandomAirport()
    # Airline Info
    carrier_code = random_flight["OperatingCarrier"]["AirlineID"]
    airline = codes.carrier_codes[carrier_code]["Name"]
    # Airport Info
    dest_code = random_flight["Arrival"]["AirportCode"]
    # print(dest_code)
    dest_airport_request = requests.get(
        airport_codes_url + dest_code, headers=headers, params=code_params
    )
    if dest_airport_request.status_code == requests.codes.ok:
        dest_airport_data = dest_airport_request.json()
        # check to see if it's an array or not. sometimes not an array
        if type(dest_airport_data["AirportResource"]["Airports"]["Airport"]) is list:
            dest_airport_name = dest_airport_data["AirportResource"]["Airports"]["Airport"][0]["Names"]["Name"]["$"]
        else:
            dest_airport_name = dest_airport_data["AirportResource"]["Airports"]["Airport"]["Names"]["Name"]["$"]
    else:
        textNImg.UpdateText("Start", "Destination airport error")
        textNImg.WriteAll()
        return
    flight_num = random_flight["OperatingCarrier"]["FlightNumber"]

    # Departure Info
    dept_time_obj = parse(random_flight["Departure"]["ScheduledTimeUTC"]["DateTime"])
    timezone = pytz.timezone(depart_airport_tz)
    dept_time_str = dept_time_obj.astimezone(timezone).strftime("%H:%M")
    flight_status = random_flight["Departure"]["TimeStatus"]["Code"]
    flight_status_formatted = codes.status_codes[flight_status]

    terminal_info = (
        random_flight["Departure"]["Terminal"]
        if "Terminal" in random_flight["Departure"]
        else {}
    )

    gate = " G:" + terminal_info["Gate"] if "Gate" in terminal_info else ""
    terminal_name = "T:" + terminal_info["Name"] if "Name" in terminal_info else ""
    terminal = terminal_name + " " + gate

    # Arrival Info
    arrival_time_obj = parse(random_flight["Arrival"]["ScheduledTimeUTC"]["DateTime"])
    # arrival_time_str = arrival_time_obj.strftime("%H:%M")
    flight_length_arr = str(arrival_time_obj - dept_time_obj).split(":")
    flight_length_hours = (
        flight_length_arr[0]
        if len(flight_length_arr[0]) > 1
        else "0" + flight_length_arr[0]
    )
    flight_length = flight_length_hours + ":" + flight_length_arr[1]

    local_time_str = local_time.strftime("%H:%M")
    textNImg.Clear()

    
    # textNImg.WriteAll()
    # Add base background image
    # textNImg.AddImg(
    #     "/home/pi/rpi-epaper-airport/display-background2.png",
    #     0,
    #     0,
    #     (200, 96),
    #     Id="background",
    # )

    textNImg.UpdateImg("background", "/home/pi/rpi-epaper-airport/display-background2.png")
    # formatting for display
    airline_name = airline[:14] if len(airline) > 14 else airline

    depart_airport_name_formatted = (
        depart_airport_name[:17]
        if len(depart_airport_name) > 17
        else depart_airport_name
    )
    dest_airport_name_formatted = (
        dest_airport_name[:17] if len(dest_airport_name) > 17 else dest_airport_name
    )

    # Title Line
    textNImg.AddText(
        airline_name, leftCol, titleLine, titleText, Id="Carrier", invert=True
    )
    textNImg.AddText(
        flight_num, rightCol, titleLine, titleText, Id="Flight", invert=True
    )
    # First Line
    textNImg.AddText(
        "D:" + depart_airport_name_formatted,
        firstCol,
        firstLine,
        mainText,
        Id="departAirport",
    )
    # Second Line
    textNImg.AddText(
        "A:" + dest_airport_name_formatted,
        firstCol,
        secondLine,
        mainText,
        Id="arriveAirport",
    )
    # Third Line
    textNImg.AddText(terminal, firstCol, thirdLine, mainText, Id="terminal")
    textNImg.AddText(flight_status_formatted, midCol, thirdLine, mainText, Id="status")
    # Fourth Line
    textNImg.AddText("Depart", firstCol, fourthLine, mainText, Id="depart")
    textNImg.AddText("Length", secondCol, fourthLine, mainText, Id="length")
    textNImg.AddText("Time", thirdCol, fourthLine, mainText, Id="time")
    # Fifth Line
    textNImg.AddText(dept_time_str, firstCol, fifthLine, mainText, Id="deptTime")
    textNImg.AddText(flight_length, secondCol, fifthLine, mainText, Id="flightLen")
    textNImg.AddText(local_time_str, thirdCol, fifthLine, mainText, Id="localTime")

    textNImg.WriteAll()

    sleep(240)

    

while True:
    displayFlightInfo()
    sleep(1)

