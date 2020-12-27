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
rightCol = 155

titleText = 18
mainText = 16

# Calling PapirusComposite this way will mean nothing is written to the screen until WriteAll is called
textNImg = PapirusComposite(False, rotation = 0)

# Write text to the screen at selected point, with an Id
# Nothing will show on the screen
textNImg.AddImg("./display-background2.png",0,0,(200,96), Id="background")


# Title Line
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", leftCol, titleLine,titleText, Id="Carrier" , invert=True)
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", rightCol, titleLine,titleText, Id="Flight" , invert=True)
# First Line
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", firstCol, firstLine,mainText, Id="departAirport")
# Second Line
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", firstCol, secondLine, mainText, Id="arriveAirport")
# Third Line
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", firstCol, thirdLine,mainText, Id="terminal")
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", midCol, thirdLine,mainText, Id="status")
# Fourth Line
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", firstCol, fourthLine,mainText, Id="depart")
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", secondCol, fourthLine,mainText, Id="length")
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", thirdCol, fourthLine,mainText, Id="time")
# Fifth Line
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", firstCol, fifthLine,mainText, Id="deptTime")
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", secondCol, fifthLine,mainText, Id="flightLen")
textNImg.AddText("ABCDEFGHIJKLMNOPQRSTUVWXYZ", thirdCol, fifthLine,mainText, Id="localTime")

# Add image
# Nothing will show on the screen
# textNImg.AddImg(path, posX,posY,(w,h),id)
# textNImg.AddImg("./lufthansa-logo.png",170,0,(30,30), Id="BigImg")
# Add image to the default place and size
# Nothing will show on the screen

# Now display all elements on the screen
textNImg.WriteAll()