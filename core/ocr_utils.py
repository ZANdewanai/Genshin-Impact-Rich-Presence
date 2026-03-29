"""OCR utilities for screen capture and text processing."""
import time
import numpy as np
from PIL import ImageGrab

from core.datatypes import ActivityType, DEBUG_MODE


def capture_and_process_ocr(reader, coord, allowlist, conf_thresh, activity_type, search_func, text_processor=None, debug_key=None):
    """
    Generic function to handle OCR capture, processing, and activity detection.
    
    :param reader: OCR reader instance (from ocr_engine)
    :param coord: Coordinate tuple for ImageGrab
    :param allowlist: String for OCR allowlist
    :param conf_thresh: Confidence threshold for text filtering
    :param activity_type: ActivityType enum for detection
    :param search_func: Function to search for activity data (e.g., DATA.search_location)
    :param text_processor: Optional function to process text before searching
    :param debug_key: Optional key for debug prints (e.g., 'LOCATION')
    :return: Detected activity or None
    """
    image = None
    cap = None
    try:
        image = ImageGrab.grab(bbox=coord)
        cap = np.array(image)
    except OSError:
        print("OSError: Cannot capture screen. Try running as admin if this issue persists.")
        time.sleep(1)
        return None
    except Exception as e:
        print(f"Unexpected error during image capture for {activity_type}: {e}")
        time.sleep(1)
        return None

    results = []
    try:
        results = reader.readtext(cap, allowlist=allowlist)
    except Exception as e:
        print(f"OCR Error during {activity_type} recognition: {e}")
        # Cleanup
        del cap
        if image:
            image.close()
        del image
        time.sleep(1)
        return None

    # Cleanup memory
    del cap
    if image:
        image.close()
    del image

    processed_text = " ".join([word.strip() for word in [r[1] for r in results if r[2] > conf_thresh]])
    if debug_key and DEBUG_MODE:
        print(f"{debug_key} OCR: '{processed_text}' (confidence: {[r[2] for r in results if r[2] > conf_thresh]})")

    if text_processor:
        processed_text = text_processor(processed_text)

    if len(processed_text) > 0:
        data = search_func(processed_text)
        if data:
            return data
    return None


def calculate_keyword_match_score(ocr_words, location_match, region_word):
    """
    Calculate how well OCR keywords match against a location database entry.
    Returns a score between 0.0 and 1.0 based on keyword overlap and relevance.
    """
    score = 0.0

    # Get location details for comparison
    location_name = location_match.location_name.lower() if hasattr(location_match, 'location_name') else ""
    subregion = location_match.subarea.lower() if hasattr(location_match, 'subarea') else ""
    region = location_match.country.lower() if hasattr(location_match, 'country') else ""
    match_term = location_match.search_str.lower() if hasattr(location_match, 'search_str') else ""

    # Prepare OCR words for comparison (remove punctuation, convert to lowercase)
    clean_ocr_words = [word.strip('.,!?').lower() for word in ocr_words if len(word.strip('.,!?')) > 1]

    # Score 1: Direct keyword matches with location name
    name_matches = 0
    for ocr_word in clean_ocr_words:
        if (len(ocr_word) > 2 and
            (ocr_word in location_name or
             location_name in ocr_word or
             any(ocr_word in part or part in ocr_word for part in location_name.split()))):
            name_matches += 1

    if name_matches > 0:
        score += min(0.4, name_matches * 0.2)  # Up to 40% for name matches

    # Score 2: Match term overlap (this is the key - CSV match column)
    if match_term:
        match_words = match_term.split()
        match_overlap = sum(1 for ocr_word in clean_ocr_words
                          for match_word in match_words
                          if (len(ocr_word) > 2 and len(match_word) > 2 and
                              (ocr_word == match_word or
                               ocr_word in match_word or
                               match_word in ocr_word)))
        if match_overlap > 0:
            score += min(0.5, match_overlap * 0.25)  # Up to 50% for match term overlap

    # Score 3: Region confirmation
    if region and region_word.lower() in region:
        score += 0.2  # 20% bonus for correct region

    # Score 4: Subregion relevance
    if subregion:
        subregion_matches = sum(1 for ocr_word in clean_ocr_words
                              if len(ocr_word) > 2 and ocr_word in subregion)
        if subregion_matches > 0:
            score += min(0.1, subregion_matches * 0.05)  # Up to 10% for subregion

    return max(0.0, min(1.0, score))


def calculate_location_confidence(subregion_word, region_word, original_text, pattern):
    """
    Calculate confidence score for how well a location pattern matches the OCR text.
    Returns a value between 0.0 and 1.0 where 1.0 is perfect confidence.
    """
    confidence = 0.0
    original_lower = original_text.lower()

    # Base confidence: Both words appear in the original text
    if subregion_word.lower() in original_lower and region_word.lower() in original_lower:
        confidence += 0.4

        # Bonus: Words appear close to each other (within 15 words)
        subregion_positions = []
        region_positions = []

        words = original_text.split()
        for i, word in enumerate(words):
            if subregion_word.lower() in word.lower():
                subregion_positions.append(i)
            if region_word.lower() in word.lower():
                region_positions.append(i)

        # Check if any subregion and region appear close together
        for sub_pos in subregion_positions:
            for reg_pos in region_positions:
                distance = abs(sub_pos - reg_pos)
                if distance <= 15:  # Within reasonable proximity
                    proximity_bonus = max(0, (15 - distance) / 15) * 0.3
                    confidence += proximity_bonus

        # Bonus: Pattern matches expected format
        if ', ' in pattern:  # Proper "Subregion, Region" format
            confidence += 0.2
        elif pattern.count(' ') <= 2:  # Simple format
            confidence += 0.1

        # Bonus: Subregion and region words are distinct and meaningful
        if (len(subregion_word) > 3 and len(region_word) > 3 and
            subregion_word.lower() != region_word.lower()):
            confidence += 0.2

    return max(0.0, min(1.0, confidence))
