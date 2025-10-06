import cv2
import time
import os

class ImageUtils:
    def __init__(self, debug_save_images: bool = False, debug_images_directory: str = "./debug_ocr"):
        self.debug_save_images = debug_save_images
        self.debug_images_directory = debug_images_directory
        self.debug_image_counter = 1

    def convert_to_grayscale(self, image):
        """Convert BGR image to grayscale."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def enhance_contrast(self, image, alpha: float = 1.2, beta: int = 10):
        """Enhance brightness and contrast for better text visibility."""
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

    def apply_binary_threshold(self, image, threshold: int = 180):
        """Apply binary threshold to isolate bright white text."""
        _, binary = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
        return binary

    def save_debug_image(self, image, step_name: str):
        """Save debug image with sequential numbering if debug mode is enabled."""
        if not self.debug_save_images:
            return

        os.makedirs(self.debug_images_directory, exist_ok=True)
        filename = f"{self.debug_images_directory}/{self.debug_image_counter:04d}_{step_name}.png"
        self.debug_image_counter += 1

        if len(image.shape) == 3 and image.shape[2] == 3:
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, image_bgr)
        else:
            cv2.imwrite(filename, image)

        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [DEBUG] Saved {filename}")

    def preprocess_for_ocr(self, image, debug_info: str = ""):
        """Full preprocessing pipeline using helpers."""
        if self.debug_save_images:
            self.save_debug_image(image, f"00_original_{debug_info}")

        gray = self.convert_to_grayscale(image)
        enhanced = self.enhance_contrast(gray)

        if self.debug_save_images:
            self.save_debug_image(enhanced, f"01_enhanced_{debug_info}")

        binary = self.apply_binary_threshold(enhanced)

        if self.debug_save_images:
            self.save_debug_image(binary, f"02_binary_{debug_info}")

        return binary
