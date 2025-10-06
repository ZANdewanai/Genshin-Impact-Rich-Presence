import cv2
import numpy as np
import matplotlib.pyplot as plt
import sys
import time
import os
import tempfile
import shutil
from PIL import ImageGrab
import pytesseract

def setup_tesseract_cmd():
    """Set up tesseract command path for both script and EXE environments."""
    if getattr(sys, 'frozen', False):
        # Running as bundled EXE
        base_path = sys._MEIPASS
        tesseract_path = os.path.join(base_path, "tesseract", "tesseract.exe")

        # Extract tesseract to temp if not already there
        temp_dir = os.path.join(tempfile.gettempdir(), "genshin_tesseract")
        os.makedirs(temp_dir, exist_ok=True)

        temp_tesseract_exe = os.path.join(temp_dir, "tesseract.exe")

        if not os.path.exists(temp_tesseract_exe):
            print("Extracting tesseract to temp directory...")
            # Copy tesseract executable
            if os.path.exists(tesseract_path):
                shutil.copy2(tesseract_path, temp_tesseract_exe)

            # Copy tesseract data folder if it exists
            tesseract_data_src = os.path.join(base_path, "tesseract")
            if os.path.exists(tesseract_data_src):
                tesseract_data_dst = os.path.join(temp_dir, "tessdata")
                os.makedirs(tesseract_data_dst, exist_ok=True)
                for item in os.listdir(tesseract_data_src):
                    src_item = os.path.join(tesseract_data_src, item)
                    dst_item = os.path.join(tesseract_data_dst, item)
                    if os.path.isdir(src_item):
                        shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src_item, dst_item)

        # Set TESSDATA_PREFIX environment variable
        tessdata_path = os.path.join(temp_dir, "tessdata")
        if os.path.exists(tessdata_path):
            os.environ["TESSDATA_PREFIX"] = temp_dir

        return temp_tesseract_exe
    else:
        # Running as regular script
        return r"tesseract\tesseract.exe"

# Set up tesseract
pytesseract.pytesseract.tesseract_cmd = setup_tesseract_cmd()

def wait_for_enter(step_name):
    """Wait for Enter key press and show step info"""
    print(f"\n[Step] {step_name}")
    print("Press Enter to continue (or Ctrl+C to exit)...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nExiting...")
        plt.close('all')
        sys.exit(0)

def show_image(title, image, is_bgr=True):
    """Display an image with the given title"""
    plt.figure(figsize=(10, 6))
    
    if is_bgr and len(image.shape) == 3:  # Convert BGR to RGB for display
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    if len(image.shape) == 2:  # Grayscale
        plt.imshow(image, cmap='gray')
    else:  # Color
        plt.imshow(image)
    
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    plt.show(block=False)
    
    wait_for_enter(title)
    plt.close()

def preprocess_image_for_ocr(image):
    """Simplified preprocessing focusing only on white text detection"""
    show_image("1. Original Image", image.copy())
    
    # 1. Convert to HSV color space for better color-based segmentation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 2. Define range for white text (nearly white, low saturation)
    lower_white = np.array([0, 0, 240], dtype=np.uint8)  # Very high value threshold for bright white
    upper_white = np.array([180, 15, 255], dtype=np.uint8)  # Very low saturation for true white
    
    # 3. Create and show the white text mask
    white_mask = cv2.inRange(hsv, lower_white, upper_white)
    show_image("2. White Text Mask (HSV)", white_mask, is_bgr=False)
    wait_for_enter("White Text Mask")
    
    # 4. Create black text on white background (Tesseract's preferred format)
    final = np.ones_like(image) * 255  # White background
    final[white_mask == 255] = [0, 0, 0]  # Black text
    
    # 5. Convert to grayscale for display
    final_gray = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
    show_image("3. Final: Black Text on White Background", final_gray, is_bgr=False)

    # 6. OCR Analysis - Test different PSM modes
    print("\n=== OCR ANALYSIS ===")
    psm_modes = [3, 6, 7, 8, 10, 11, 13]

    print("Testing different PSM modes on processed image:")
    for psm in psm_modes:
        try:
            result = pytesseract.image_to_string(
                final_gray,
                config=f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ',
                timeout=2
            ).strip()
            print(f"PSM {psm:2d}: '{result}'")
        except Exception as e:
            print(f"PSM {psm:2d}: ERROR - {str(e)[:50]}...")

    # Find best result
    best_result = ""
    best_psm = -1
    for psm in psm_modes:
        try:
            result = pytesseract.image_to_string(
                final_gray,
                config=f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ',
                timeout=2
            ).strip()
            if len(result) > len(best_result):
                best_result = result
                best_psm = psm
        except:
            continue

    if best_result:
        print(f"\nBest OCR result: '{best_result}' (PSM {best_psm})")
    else:
        print("\nNo valid OCR results found")

    return final_gray

def process_image(image_path):
    """Process an image file through the pipeline"""
    try:
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not read image: {image_path}")
            return
        
        print("Starting OCR Preprocessing Visualization")
        print("=" * 40)
        print("Press Enter to step through each processing stage")
        print("Press Ctrl+C at any time to exit")
        print("=" * 40)
        
        # Run the preprocessing pipeline
        preprocess_image_for_ocr(image)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        plt.close('all')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_image(sys.argv[1])
    else:
        print("Please provide an image path as an argument")
        print("Usage: python visualize_ocr_preprocessing.py path/to/your/image.png")
