"""OCR utilities for screen capture and text processing."""

import time
import numpy as np
from PIL import ImageGrab, Image

from core.datatypes import ActivityType, DEBUG_MODE
from core.log_utils import log, should_log, record_ocr


def capture_and_process_ocr(
    reader,
    coord,
    allowlist,
    conf_thresh,
    activity_type,
    search_func,
    text_processor=None,
    debug_key=None,
    image=None,
    scale=0.5,
):
    """
    Generic function to handle OCR capture, processing, and activity detection.

    :param reader: OCR reader instance (from ocr_engine)
    :param coord: Coordinate tuple for ImageGrab or crop region
    :param allowlist: String for OCR allowlist
    :param conf_thresh: Confidence threshold for text filtering
    :param activity_type: ActivityType enum for detection
    :param search_func: Function to search for activity data (e.g., DATA.search_location)
    :param text_processor: Optional function to process text before searching
    :param debug_key: Optional key for debug prints (e.g., 'LOCATION')
    :param image: Optional pre-captured PIL Image. If provided, coord is used to crop
                  from this image instead of doing a new screen capture. The caller
                  remains responsible for closing the original image.
    :return: Detected activity or None
    """
    source_image = None
    cap = None
    try:
        if image is None:
            time.sleep(0.01)
            source_image = ImageGrab.grab(bbox=coord)
        else:
            source_image = image.crop(coord)

        grayscale = source_image.convert('L')
        small_image = grayscale.resize(
            (max(1, int(grayscale.width * scale)), max(1, int(grayscale.height * scale))), Image.LANCZOS
        )
        cap = np.array(small_image)
        grayscale.close()
        small_image.close()
    except OSError:
        if source_image:
            source_image.close()
        print(
            "OSError: Cannot capture screen. Try running as admin if this issue persists."
        )
        time.sleep(1)
        return None
    except RuntimeError as e:
        if source_image:
            source_image.close()
        print(f"Screen capture runtime error during {activity_type}: {e}")
        time.sleep(1)
        return None

    results = []
    _ocr_start = time.perf_counter()
    try:
        results = reader.readtext(cap, allowlist=allowlist)
    except RuntimeError as e:
        print(f"OCR RuntimeError during {activity_type} recognition: {e}")
        del cap
        if source_image:
            source_image.close()
        del source_image
        time.sleep(1)
        return None

    # Perf counter: measure pure OCR inference time per region
    record_ocr(
        debug_key or activity_type.name,
        (time.perf_counter() - _ocr_start) * 1000.0,
    )

    del cap
    if source_image:
        source_image.close()
    del source_image

    processed_text = " ".join(
        [word.strip().replace('\n', ' ').replace('\r', ' ') for word in [r[1] for r in results if r[2] > conf_thresh]]
    )
    if debug_key and DEBUG_MODE:
        # Only log non-empty reads immediately; throttle identical empty
        # reads to once per 10s per region to avoid console spam
        if processed_text or should_log(f"ocr_empty_{debug_key}", 10.0):
            log(
                f"{debug_key} OCR: '{processed_text}' "
                f"(confidence: {[r[2] for r in results if r[2] > conf_thresh]})"
            )

    if text_processor:
        processed_text = text_processor(processed_text)

    if len(processed_text) > 0:
        data = search_func(processed_text)
        if data:
            return data
    return None


def process_map_text(text, search_index):
    """Process map location OCR text to extract location candidates."""
    if not text or not text.strip():
        return ""

    # Handle text duplication issue - remove repeated patterns
    cleaned_text = " ".join(text.replace("\n", " ").split())

    # Remove duplicated substrings
    words = cleaned_text.split()
    if (
        len(words) > 10
    ):  # Only process if we have a lot of words (indicating possible duplication)
        result_words = []
        i = 0
        while i < len(words):
            current_word = words[i]
            found_repetition = False
            for length in range(
                min(8, len(words) - i - 1), 2, -1
            ):  # Try different sequence lengths
                if i + length * 2 <= len(words):
                    seq1 = " ".join(words[i : i + length])
                    seq2 = " ".join(words[i + length : i + length * 2])
                    if (
                        seq1 == seq2 and len(seq1) > 10
                    ):  # Only remove substantial repetitions
                        if DEBUG_MODE:
                            print(
                                f"[FILTER] MAP_LOC: Found repetition, removing duplicate sequence: '{seq1}'"
                            )
                        i += length * 2  # Skip both occurrences
                        found_repetition = True
                        break
            if not found_repetition:
                result_words.append(current_word)
                i += 1
        if result_words:
            cleaned_text = " ".join(result_words)
        else:
            cleaned_text = " ".join(
                words
            )  # Fallback to original if deduplication fails

    # Split into words for better processing
    words = cleaned_text.split()
    if not words:
        return ""

    # Filter out only the most obvious OCR artifacts
    filtered_words = []
    skip_words = {
        "d",
        "that",
        "are",
        "of",
        "the",
        "and",
        "or",
        "but",
        "with",
        "for",
        "from",
        "this",
        "these",
        "those",
        "menu",
        "exit",
        "close",
        "ok",
        "cancel",
        "select",
        "ready",
        "waiting",
        "s",
        "t",
        "re",
        "ve",
        "ll",
        "m",
        "n",  # Common OCR fragments
    }

    # Keep location-related words for pattern reconstruction
    location_context_words = {"town", "city", "village"}

    for word in words:
        word_lower = word.lower()
        # Skip very short words, common artifacts, and UI words
        if (
            len(word) < 2
            or word_lower in skip_words
            or word.isdigit()
            or (
                len(word) <= 3
                and not word[0].isupper()
                and word_lower not in location_context_words
            )
        ):
            continue
        # Clean up words that end with comma but are otherwise good
        clean_word = word.rstrip(",") if word.endswith(",") and len(word) > 3 else word
        if len(clean_word) >= 2:
            filtered_words.append(clean_word)

    if not filtered_words:
        return ""

    # Try multiple candidate extractions and validate against database
    candidates = []

    # Pattern 1: Look for proper noun combinations (capitalized words)
    proper_nouns = [
        word for word in filtered_words if word[0].isupper() and len(word) > 2
    ]

    if len(proper_nouns) >= 2:
        # Try combinations of 2-3 proper nouns
        for i in range(len(proper_nouns) - 1):
            for j in range(i + 1, min(i + 3, len(proper_nouns))):
                combination = " ".join(proper_nouns[i : j + 1])
                if 5 < len(combination) < 50:  # Reasonable length for location name
                    candidates.append(combination)

    # Pattern 2: Try mixed case word combinations
    if len(filtered_words) >= 2:
        # Try 2-word combinations
        for i in range(len(filtered_words) - 1):
            combination = f"{filtered_words[i]} {filtered_words[i + 1]}"
            if 5 < len(combination) < 40:
                candidates.append(combination)

        # Try 3-word combinations if available
        if len(filtered_words) >= 3:
            for i in range(len(filtered_words) - 2):
                combination = f"{filtered_words[i]} {filtered_words[i + 1]} {filtered_words[i + 2]}"
                if 5 < len(combination) < 50:
                    candidates.append(combination)

    # Pattern 3: Single proper nouns
    for word in proper_nouns:
        if 3 < len(word) < 30:
            candidates.append(word)

    # Pattern 4: Single filtered words
    for word in filtered_words:
        if 3 < len(word) < 30:
            candidates.append(word)

    # Cross-check each candidate against the locations database
    for candidate in candidates:
        # Try exact match first
        location_match = search_index.search_location(candidate)
        if location_match:
            if DEBUG_MODE:
                print(
                    f"[OK] MAP_LOC: Found database match for '{candidate}' -> '{location_match.location_name}'"
                )
            return candidate

        # Try partial matches with database entries
        for word in candidate.split():
            if len(word) > 3:  # Only try meaningful words
                location_match = search_index.search_location(word)
                if location_match:
                    if DEBUG_MODE:
                        print(
                            f"[OK] MAP_LOC: Found partial database match for '{word}' in '{candidate}' -> '{location_match.location_name}'"
                        )
                    return candidate

    # No valid location found
    if DEBUG_MODE and should_log("maploc_error", 15.0):
        log(
            f"[ERROR] MAP_LOC: No database matches for candidates from '{cleaned_text}'"
        )
    # Return cleaned text instead of empty string to allow search_func to try fuzzy matching
    return cleaned_text
