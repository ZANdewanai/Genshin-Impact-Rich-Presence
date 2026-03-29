"""
Live OCR testing tool with cv2 preview windows.
Displays captured regions in real-time for coordinate verification.

Usage: python tools/test_imagegrab.py
Press ESC to exit.
"""

from typing import Text
import cv2
import numpy as np
import easyocr
import time
import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# We only need the ImageGrab class from PIL
from PIL import ImageGrab

from CONFIG import (
    NUMBER_4P_COORD, NAMES_4P_COORD, ACTIVE_CHARACTER_THRESH,
    NAME_CONF_THRESH, LOCATION_COORD, BOSS_COORD, DOMAIN_COORD,
    PARTY_SETUP_COORD, OCR_CHARNAMES_ONE_IN, OCR_LOC_ONE_IN,
    OCR_BOSS_ONE_IN, OCR_DOMAIN_ONE_IN, ALLOWLIST, ALLOWLIST2,
    DEBUG_MODE, INACTIVE_COOLDOWN, LOC_CONF_THRESH
)

reader = easyocr.Reader(["en"], gpu=False)

# Set to True to popup windows displaying captured images to double check coordinates.
# Only useful if you are using 2 monitors.
# Setting too many to True may cause lag.
SHOW_CHARACTERS = False
SHOW_LOC = True
SHOW_BOSS = False
SHOW_DOMAIN = False
SHOW_PARTY_SETUP = False

if __name__ == "__main__": # run only if this file is explicitly being run
    current_active_character = 0 # 1-indexed. 0 is none.
    curr_char_names = ["", "", "", ""]
    curr_loc = "" # Location/boss/domain name
    game_paused = False
    domain_cooldown = 0
    loop_count = 0
    
    while True:
        loop_count += 1
        
        curr_game_paused = False # logic state variable to compare with game_paused
        
        #### CAPTURE ACTIVE CHARACTER (every loop)
        
        try:
            # NUMBER_4P_COORD now contains 4-tuple bounding boxes (x1, y1, x2, y2)
            # Use a fixed offset point within the box for brightness detection
            charnumber_cap = [
                ImageGrab.grab(bbox=(
                    NUMBER_4P_COORD[i][0] + 15,
                    NUMBER_4P_COORD[i][1] + 15,
                    NUMBER_4P_COORD[i][0] + 16,
                    NUMBER_4P_COORD[i][1] + 16
                )).getpixel((0,0))
                for i in range(4)
            ]
        except OSError:
            print("OSError: Cannot capture screen. Try running as admin if this issue persists.")
            time.sleep(100)
            continue
        
        charnumber_brightness = [sum(rgb) for rgb in charnumber_cap]
        active_character = [idx for idx, bri in enumerate(charnumber_brightness) if bri < ACTIVE_CHARACTER_THRESH]
        found_active_character = len(active_character) == 1
        
        if found_active_character and active_character[0] + 1 != current_active_character:
            current_active_character = active_character[0] + 1
            print(f'Switched active character to "{curr_char_names[current_active_character - 1]}"')
        
        if not found_active_character and current_active_character != 0:
            current_active_character = 0
            print(f'Cannot find active character: {active_character}')
        
        if found_active_character:
            domain_cooldown = 0 # reset anti-domain read cooldown
            
            #### CAPTURE PARTY MEMBERS
            
            if loop_count % OCR_CHARNAMES_ONE_IN == 0 or len([a for a in curr_char_names if a == ""]) > 0:
                try:
                    charname_cap = [np.array(ImageGrab.grab(bbox=NAMES_4P_COORD[i])) for i in range(4)]
                except OSError:
                    print("OSError: Cannot capture screen. Try running as admin if this issue persists.")
                    time.sleep(100)
                    continue
                
                # print(charnumber_brightness)
                
                if SHOW_CHARACTERS:
                    display_chars = np.concatenate(charname_cap, axis=1)
                    cv2.imshow("Character Names (ESC to close)", display_chars)

                # ([bbox top left, top right, bottom right, bottom left], text, confidence)
                char_results = [reader.readtext(img, allowlist=ALLOWLIST, ) for img in charname_cap]

                for idx, result in enumerate(char_results):
                    if len(result) > 0:
                        text = ' '.join([word.strip() for word in [r[1] for r in result]])
                        avg_conf = sum([r[2] for r in result]) / len(result)
                        
                        if avg_conf > NAME_CONF_THRESH and curr_char_names[idx] != text:
                            curr_char_names[idx] = text
                            print(f'Detected character {idx + 1}: {text}')
            
            #### CAPTURE LOCATION
            
            if loop_count % OCR_LOC_ONE_IN == 0:
                try:
                    loc_cap = np.array(ImageGrab.grab(bbox=LOCATION_COORD))
                except OSError:
                    print("OSError: Cannot capture screen. Try running as admin if this issue persists.")
                    time.sleep(100)
                    continue
                
                if SHOW_LOC:
                    cv2.imshow("Location (ESC to close)", loc_cap)
                
                loc_results = reader.readtext(loc_cap, allowlist=ALLOWLIST)
                
                loc_text = ' '.join([word.strip() for word in [r[1] for r in loc_results if r[2] > LOC_CONF_THRESH]])
                if len(loc_text) > 0:
                    if 'mission accept' in loc_text.lower():
                        if curr_loc != 'commission':
                            curr_loc = 'commission'
                            print('Detected COMMISSION')
                    elif curr_loc != loc_text:
                        curr_loc = loc_text
                        print(f'Detected location: {curr_loc}')
            
            #### CAPTURE BOSS
            
            if loop_count % OCR_BOSS_ONE_IN == 0:
                try:
                    boss_cap = np.array(ImageGrab.grab(bbox=BOSS_COORD))
                except OSError:
                    print("OSError: Cannot capture screen. Try running as admin if this issue persists.")
                    time.sleep(100)
                    continue
                
                if SHOW_BOSS:
                    cv2.imshow("Boss (ESC to close)", boss_cap)
                
                boss_results = reader.readtext(boss_cap, allowlist=ALLOWLIST)
                
                boss_text = ' '.join([word.strip() for word in [r[1] for r in boss_results if r[2] > LOC_CONF_THRESH]])
                if len(boss_text) > 0 and curr_loc != boss_text:
                    curr_loc = boss_text
                    print(f'Detected boss: {curr_loc}')
                    
        elif not found_active_character:
            curr_game_paused = True # Set False later if domain/party setup detected.
            
            domain_cooldown = max(0, domain_cooldown - 1)
            
            #### CAPTURE PARTY SETUP TEXT
            
            try:
                party_cap = np.array(ImageGrab.grab(bbox=PARTY_SETUP_COORD))
            except OSError:
                print("OSError: Cannot capture screen. Try running as admin if this issue persists.")
                time.sleep(100)
                continue
            
            if SHOW_PARTY_SETUP:
                cv2.imshow("Party Setup text (ESC to close)", party_cap)
            
            party_results = reader.readtext(party_cap, allowlist=ALLOWLIST)
            
            party_text = ' '.join([word.strip() for word in [r[1] for r in party_results if r[2] > LOC_CONF_THRESH]])
            if 'party setup' in party_text.lower():
                curr_game_paused = False
                domain_cooldown = INACTIVE_COOLDOWN
                if curr_loc != party_text:
                    curr_loc = 'Party Setup'
                    print('Entered Party Setup')
            
            #### CAPTURE DOMAIN
            if domain_cooldown == 0:
                # Prevent capturing domain if in party setup,
                # otherwise 4th character's name will be captured as domain.
                try:
                    domain_cap = np.array(ImageGrab.grab(bbox=DOMAIN_COORD))
                except OSError:
                    print("OSError: Cannot capture screen. Try running as admin if this issue persists.")
                    time.sleep(100)
                    continue
                
                if SHOW_DOMAIN:
                    cv2.imshow("Domain (ESC to close)", domain_cap)
                
                domain_results = reader.readtext(domain_cap, allowlist=ALLOWLIST)
                
                domain_text = ' '.join([word.strip() for word in [r[1] for r in domain_results if r[2] > LOC_CONF_THRESH]])
                if len(domain_text) > 0 and curr_loc != domain_text:
                    curr_loc = domain_text
                    curr_game_paused = False
                    print(f'Detected domain: {curr_loc}')
        
        if curr_game_paused != game_paused:
            if curr_game_paused:
                print('Game paused.')
            else:
                print('Game resumed.')
            game_paused = curr_game_paused
            
        # Break while loop when escape pressed (27)
        # wait 100ms between reads
        if cv2.waitKey(50) == 27:
            break

    # This will make sure all windows created from cv2 is destroyed
    cv2.destroyAllWindows()
