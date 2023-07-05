# OCR Screen Scanner
# By Dornu Inene
# Libraries that you show have all installed
from typing import Text
import cv2
import numpy as np
import pytesseract

# We only need the ImageGrab class from PIL
from PIL import ImageGrab

# Run forever unless you press Esc
while True:
    # This instance will generate an image from
    # the point of (115, 143) and (569, 283) in format of (x, y)
    cap = ImageGrab.grab(bbox=(0, 0, 2200, 400))

    # For us to use cv2.imshow we need to convert the image into a numpy array
    cap_arr = np.array(cap)

    # This isn't really needed for getting the text from a window but
    # It will show the image that it is reading it from

    # cv2.imshow() shows a window display and it is using the image that we got
    # use array as input to image
    cv2.imshow("GenshinRPC Grabs the Area you are on(close with ESC if you want to stop it)", cap_arr)

    # Read the image that was grabbed from ImageGrab.grab using    pytesseract.image_to_string
    # This is the main thing that will collect the text information from that specific area of the window
    text = pytesseract.image_to_string(cap)

    # This just removes spaces from the beginning and ends of text
    # and makes the the it reads more clean
    text = text.strip()

    # If any text was translated from the image, print it
    if len(text) > 0:
        print(text,
        file=open("player.log", "a"))

    # This line will break the while loop when you press Esc
    if cv2.waitKey(1) == 27:
        break

# This will make sure all windows created from cv2 is destroyed
cv2.destroyAllWindows()