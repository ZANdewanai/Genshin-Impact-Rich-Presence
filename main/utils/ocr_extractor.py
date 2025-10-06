import pytesseract
import cv2
import string
from typing import Optional, Tuple, Union, List
from concurrent.futures import ThreadPoolExecutor, as_completed

class OCRExtractor:
    def clean_ocr_text(self, text: str) -> str:
        """
        Clean and preprocess OCR text to improve matching accuracy.

        Args:
            text: The raw text from OCR

        Returns:
            str: Cleaned and preprocessed text, or empty string if invalid
        """
        if not text or not isinstance(text, str):
            return ""

        # Remove any non-printable characters except basic punctuation
        printable = set(string.ascii_letters + string.digits + " '-,.()")
        cleaned = ''.join(filter(lambda x: x in printable, text))

        # Remove single/double character words that aren't actual words
        words = [word for word in cleaned.split()
                 if len(word) > 2 or word.lower() in {'in', 'at', 'on', 'to', 'of', 'a', 'an', 'as'}]

        # Reconstruct the text
        cleaned = ' '.join(words).strip()

        # Check if the text contains a reasonable number of valid characters
        if len(cleaned) < 3:
            return ""

        # Check if the text has enough alphabetic characters
        if sum(c.isalpha() for c in cleaned) < 3:
            return ""

        # Check for repeated characters (e.g., 'aaaaa' or 'asdfghjkl')
        if any(3 * c in cleaned.lower() for c in set(cleaned.lower())):
            return ""

        return cleaned

    def extract_text_from_image(self, image, config: str = "",
                               preprocess: bool = True) -> str:
        """
        Extract text from an image using OCR with multiple PSM modes for better detection.

        Args:
            image: Input image (BGR format)
            config: Tesseract configuration string
            preprocess: Whether to apply preprocessing

        Returns:
            Extracted text string
        """
        try:
            if preprocess:
                # Assuming ImageUtils is available; for now, use basic preprocessing
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                processed_image = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
                _, processed_image = cv2.threshold(processed_image, 180, 255, cv2.THRESH_BINARY)
            else:
                processed_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Try multiple PSM modes for better text detection
            psm_modes = [
                (7, "--psm 7"),  # Single text line (default)
                (6, "--psm 6"),  # Uniform block of text
                (8, "--psm 8"),  # Single word
                (13, "--psm 13"), # Raw line
                (11, "--psm 11"), # Sparse text
            ]

            best_text = ""
            best_length = 0

            for psm_mode, psm_config in psm_modes:
                try:
                    # Combine user config with PSM mode
                    full_config = f"{psm_config} {config}".strip()

                    # Extract text using tesseract
                    text = pytesseract.image_to_string(processed_image, config=full_config)

                    # Clean the text
                    cleaned = self.clean_ocr_text(text)

                    if len(cleaned) > best_length:
                        best_text = cleaned
                        best_length = len(cleaned)

                except Exception:
                    continue

            return best_text.strip()

        except Exception:
            return ""

    def extract_text_from_region(self, region_bbox: Union[Tuple, List],
                                config: str = "", preprocess: bool = True,
                                game_window_rect: Optional[Tuple] = None, capture_utils=None) -> str:
        """
        Extract text from a specific screen region.

        Args:
            region_bbox: Region coordinates
            config: Tesseract configuration string
            preprocess: Whether to apply preprocessing
            game_window_rect: Game window rectangle
            capture_utils: Instance of CaptureUtils for capturing

        Returns:
            Extracted text string
        """
        if capture_utils is None:
            return ""
        # Capture the region
        image = capture_utils.capture_game_region(region_bbox, game_window_rect)
        if image is None:
            return ""
        return self.extract_text_from_image(image, config, preprocess)

    def extract_text_from_region_parallel(self, region_bbox: Union[Tuple, List],
                                          config: str = "", preprocess: bool = True,
                                          game_window_rect: Optional[Tuple] = None,
                                          num_captures: int = 6, capture_utils=None) -> str:
        """
        Extract text using PARALLEL processing architecture.

        Args:
            region_bbox: Region coordinates
            config: Tesseract configuration string
            preprocess: Whether to apply preprocessing
            game_window_rect: Game window rectangle
            num_captures: Number of rapid screenshots to take
            capture_utils: Instance of CaptureUtils for capturing

        Returns:
            Extracted text string (best result from all attempts)
        """
        if capture_utils is None:
            return ""

        # Step 1: Take multiple screenshots RAPIDLY
        images = []
        for i in range(num_captures):
            image = capture_utils.capture_game_region(region_bbox, game_window_rect)
            if image is not None:
                images.append((image, i))

        if not images:
            return ""

        # Step 2: Process all screenshots in PARALLEL
        def process_single_image(img_data):
            image, index = img_data
            text = self.extract_text_from_image(image, config, preprocess)
            cleaned = self.clean_ocr_text(text)
            return cleaned, len(cleaned), index

        best_text = ""
        best_length = 0
        best_index = -1

        with ThreadPoolExecutor(max_workers=min(len(images), 4)) as executor:
            future_to_image = {
                executor.submit(process_single_image, img_data): img_data
                for img_data in images
            }

            for future in as_completed(future_to_image):
                try:
                    cleaned, length, index = future.result()
                    if length > best_length:
                        best_text = cleaned
                        best_length = length
                        best_index = index
                except Exception:
                    continue

        return best_text.strip()
