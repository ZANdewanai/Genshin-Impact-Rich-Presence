"""
OCR Engine module for Genshin Impact Rich Presence.

Handles screen capture, image preprocessing, and OCR text extraction.
"""

import os
import sys
import tempfile
import time
import numpy as np
from typing import Optional, Tuple, Union, List

# Import new modules
from ...utils.image_utils import ImageUtils
from ...utils.capture_utils import CaptureUtils
from ...utils.ocr_extractor import OCRExtractor


class OCREngine:
    """
    Handles OCR operations including screen capture and text extraction.
    """

    def __init__(self, debug_mode: bool = False, debug_save_images: bool = False,
                 debug_images_directory: str = "./debug_ocr", game_state_detector=None):
        """
        Initialize OCR engine.

        Args:
            debug_mode: Enable debug output
            debug_save_images: Enable saving debug images
            debug_images_directory: Directory to save debug images
            game_state_detector: GameStateDetector instance
        """
        self.debug_mode = debug_mode
        self.debug_save_images = debug_save_images
        self.debug_images_directory = debug_images_directory
        self.game_state_detector = game_state_detector

        # Initialize sub-modules
        self.image_utils = ImageUtils(debug_save_images, debug_images_directory)
        self.capture_utils = CaptureUtils(debug_mode)
        self.ocr_extractor = OCRExtractor()

        # Tesseract setup
        self._setup_tesseract()

    def _setup_tesseract(self):
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

            pytesseract.pytesseract.tesseract_cmd = temp_tesseract_exe
            # Running as regular script
            pytesseract.pytesseract.tesseract_cmd = r"tesseract\tesseract.exe"

    def capture_game_region(self, region_bbox: Union[Tuple, List],
                           game_window_rect: Optional[Tuple] = None) -> Optional[np.ndarray]:
        """Delegate to CaptureUtils."""
        return self.capture_utils.capture_game_region(region_bbox, game_window_rect)

    def _get_game_window_rect(self) -> Optional[Tuple]:
        """Delegate to CaptureUtils."""
        return self.capture_utils._get_game_window_rect()

    def _is_game_focused(self) -> bool:
        """Delegate to CaptureUtils."""
        return self.capture_utils._is_game_focused()

    def _capture_screen_region(self, bbox: Tuple) -> Optional[np.ndarray]:
        """Delegate to CaptureUtils."""
        return self.capture_utils._capture_screen_region(bbox)

    def preprocess_image_for_ocr(self, image: np.ndarray, debug_info: str = "") -> np.ndarray:
        """
        Enhanced preprocessing for better white text extraction in Genshin Impact.
        Uses HSV color space to specifically target bright white text with low saturation.

        Args:
            image: Input BGR image
            debug_info: Optional debug information to include in saved filenames

        Returns:
            Preprocessed grayscale image ready for OCR
        """
        # Check if we should save debug images for this specific region
        should_save_debug = self.debug_save_images

        if debug_info and hasattr(self, 'game_state_detector'):
            # Check individual component debug flags
            detector = self.game_state_detector
            if debug_info.startswith('location') and hasattr(detector, 'debug_location'):
                should_save_debug = should_save_debug and detector.debug_location
            elif debug_info.startswith('character') and hasattr(detector, 'debug_character'):
                should_save_debug = should_save_debug and detector.debug_character
            elif debug_info == 'boss' and hasattr(detector, 'debug_boss'):
                should_save_debug = should_save_debug and detector.debug_boss
            elif debug_info == 'domain' and hasattr(detector, 'debug_domain'):
                should_save_debug = should_save_debug and detector.debug_domain
            elif debug_info == 'game_menu' and hasattr(detector, 'debug_game_menu'):
                should_save_debug = should_save_debug and detector.debug_game_menu

        # Use ImageUtils for preprocessing
        self.image_utils.debug_save_images = should_save_debug
        return self.image_utils.preprocess_for_ocr(image, debug_info)

    def clean_ocr_text(self, text: str) -> str:
        """Delegate to OCRExtractor."""
        return self.ocr_extractor.clean_ocr_text(text)

    def extract_text_from_image(self, image: np.ndarray, config: str = "",
                               preprocess: bool = True, region_name: str = "") -> str:
        """Delegate to OCRExtractor."""
        return self.ocr_extractor.extract_text_from_image(image, config, preprocess)

    def extract_text_from_region(self, region_bbox: Union[Tuple, List],
                                config: str = "", preprocess: bool = True,
                                game_window_rect: Optional[Tuple] = None) -> str:
        """Delegate to OCRExtractor."""
        return self.ocr_extractor.extract_text_from_region(region_bbox, config, preprocess, game_window_rect, self.capture_utils)

    def debug_capture_all_regions(self, regions_dict: dict) -> dict:
        """
        Debug method to capture and analyze all OCR regions.

        Args:
            regions_dict: Dictionary of region names to coordinates

        Returns:
            Dictionary with capture results and analysis
        """
        if not self.debug_mode:
            print("[DEBUG] Debug mode not enabled")
            return {}

        results = {}

        print(f"\n{'='*60}")
        print("OCR ENGINE DEBUG - CAPTURING ALL REGIONS")
        print(f"{'='*60}")

        for region_name, coords in regions_dict.items():
            print(f"\n--- Testing {region_name.upper()} ---")

            if not coords or len(coords) < 4:
                print(f"   ✗ Invalid coordinates: {coords}")
                results[region_name] = {"error": "Invalid coordinates"}
                continue

            # Capture region
            image = self.capture_game_region(coords)
            if image is None:
                print(f"   ✗ Failed to capture {region_name}")
                results[region_name] = {"error": "Capture failed"}
                continue

            print(f"   ✓ Captured: {image.shape}")

            # Test preprocessing
            try:
                processed = self.preprocess_image_for_ocr(image, region_name)
                print(f"   ✓ Preprocessed: {processed.shape}")
            except Exception as e:
                print(f"   ✗ Preprocessing failed: {e}")
                processed = None

            # Test OCR with multiple configurations
            ocr_configs = [
                "--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
                "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
                "--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
                "--psm 6",  # Default
            ]

            ocr_results = []
            for i, config in enumerate(ocr_configs):
                try:
                    if processed is not None:
                        text = self.extract_text_from_image(processed, config, preprocess=False, region_name=region_name)
                        cleaned = self.clean_ocr_text(text)
                        ocr_results.append({
                            "config": config,
                            "raw_text": text,
                            "cleaned_text": cleaned,
                            "length": len(cleaned)
                        })
                        print(f"   Config {i+1}: '{cleaned}' (len={len(cleaned)})")
                except Exception as e:
                    print(f"   ✗ OCR config {i+1} failed: {e}")

            # Find best result
            if ocr_results:
                best_result = max(ocr_results, key=lambda x: x["length"])
                print(f"   🏆 Best result: '{best_result['cleaned_text']}' (len={best_result['length']})")

                results[region_name] = {
                    "captured": True,
                    "shape": image.shape,
                    "preprocessed": processed is not None,
                    "ocr_results": ocr_results,
                    "best_result": best_result
                }
            else:
                results[region_name] = {
                    "captured": True,
                    "shape": image.shape,
                    "preprocessed": processed is not None,
                    "error": "No OCR results"
                }

        # Summary
        self._print_debug_summary(results)
        return results

    def _print_debug_summary(self, results: dict):
        """Print a summary of debug results."""
        print(f"\n{'='*60}")
        print("OCR ENGINE DEBUG SUMMARY")
        print(f"{'='*60}")

        successful_captures = sum(1 for r in results.values() if r.get("captured", False))
        successful_preprocessing = sum(1 for r in results.values() if r.get("preprocessed", False))
        regions_with_text = sum(1 for r in results.values() if r.get("best_result", {}).get("length", 0) > 0)

        print(f"Regions tested: {len(results)}")
        print(f"Successful captures: {successful_captures}")
        print(f"Successful preprocessing: {successful_preprocessing}")
        print(f"Regions with OCR text: {regions_with_text}")

        if regions_with_text > 0:
            print("\nOCR Results:")
            for region_name, result in results.items():
                best = result.get("best_result", {})
                text = best.get("cleaned_text", "")
                if text:
                    print(f"  {region_name}: '{text}'")

        if successful_captures == len(results):
            print("🎉 All regions captured successfully!")
        else:
            print("⚠️  Some regions failed to capture")

    def extract_text_from_region_parallel(self, region_bbox: Union[Tuple, List],
                                          config: str = "", preprocess: bool = True,
                                          game_window_rect: Optional[Tuple] = None,
                                          num_captures: int = 6) -> str:
        """Delegate to OCRExtractor."""
        return self.ocr_extractor.extract_text_from_region_parallel(region_bbox, config, preprocess, game_window_rect, num_captures, self.capture_utils)

    def debug_ocr_performance(self, test_iterations: int = 10) -> dict:
        """
        Debug method to test OCR performance and reliability.

        Args:
            test_iterations: Number of test iterations

        Returns:
            Performance analysis results
        """
        if not self.debug_mode:
            print("[DEBUG] Debug mode not enabled")
            return {}

        print(f"\n{'='*60}")
        print(f"OCR ENGINE DEBUG - PERFORMANCE TEST ({test_iterations} iterations)")
        print(f"{'='*60}")

        # Test coordinates (use a simple region)
        test_coords = (100, 100, 200, 150)  # Small test region

        results = {
            "capture_times": [],
            "preprocess_times": [],
            "ocr_times": [],
            "success_count": 0,
            "total_iterations": test_iterations
        }

        for i in range(test_iterations):
            iteration_start = time.time()

            # Test capture
            capture_start = time.time()
            image = self.capture_game_region(test_coords)
            capture_time = time.time() - capture_start
            results["capture_times"].append(capture_time)

            if image is None:
                print(f"   Iteration {i+1}: ✗ Capture failed ({capture_time:.4f}s)")
                continue

            # Test preprocessing
            preprocess_start = time.time()
            processed = self.preprocess_image_for_ocr(image)
            preprocess_time = time.time() - preprocess_start
            results["preprocess_times"].append(preprocess_time)

            # Test OCR
            ocr_start = time.time()
            text = self.extract_text_from_image(processed, preprocess=False, region_name="performance_test")
            ocr_time = time.time() - ocr_start
            results["ocr_times"].append(ocr_time)

            total_time = time.time() - iteration_start
            results["success_count"] += 1

            print(f"   Iteration {i+1}: ✓ ({total_time:.4f}s) - Capture: {capture_time:.4f}s, Preprocess: {preprocess_time:.4f}s, OCR: {ocr_time:.4f}s)")

        # Performance analysis
        if results["capture_times"]:
            avg_capture = sum(results["capture_times"]) / len(results["capture_times"])
            avg_preprocess = sum(results["preprocess_times"]) / len(results["preprocess_times"])
            avg_ocr = sum(results["ocr_times"]) / len(results["ocr_times"])

            print(f"\nPerformance Summary:")
            print(f"   Average capture time: {avg_capture:.4f}s")
            print(f"   Average preprocess time: {avg_preprocess:.4f}s")
            print(f"   Average OCR time: {avg_ocr:.4f}s")
            print(f"   Success rate: {results['success_count']}/{test_iterations} ({results['success_count']/test_iterations*100:.1f}%)")

            results.update({
                "avg_capture_time": avg_capture,
                "avg_preprocess_time": avg_preprocess,
                "avg_ocr_time": avg_ocr,
                "success_rate": results["success_count"] / test_iterations
            })

        return results

    def debug_specific_region(self, region_name: str, coords: tuple, config: str = "") -> dict:
        """
        Debug a specific capture region individually.

        Args:
            region_name: Name of the region being tested
            coords: Region coordinates (x, y, width, height)
            config: OCR configuration string

        Returns:
            Dictionary with debug results for this specific region
        """
        if not self.debug_mode:
            print(f"[DEBUG] Debug mode not enabled - skipping {region_name} test")
            return {}

        print(f"\n{'🔍'} DEBUGGING: {region_name.upper()}")
        print(f"{'─'*50}")

        results = {"region_name": region_name, "coords": coords}

        try:
            # Capture the region
            print("📸 Capturing region...")
            image = self.capture_game_region(coords)
            if image is None:
                print("❌ Capture failed")
                results["error"] = "Capture failed"
                return results

            print(f"✅ Captured: {image.shape}")

            # Test preprocessing
            print("🎨 Testing preprocessing...")
            processed = self.preprocess_image_for_ocr(image, region_name)
            if processed is None:
                print("❌ Preprocessing failed")
                results["error"] = "Preprocessing failed"
                return results

            print(f"✅ Preprocessed: {processed.shape}")

            # Test OCR with different PSM modes
            print("🔤 Testing OCR with multiple PSM modes...")
            psm_modes = [6, 7, 8, 11, 13]
            ocr_results = []

            for psm in psm_modes:
                try:
                    text = self.extract_text_from_image(
                        processed,
                        config=f"--psm {psm} {config}",
                        preprocess=False,
                        region_name=region_name
                    )
                    cleaned = self.clean_ocr_text(text)
                    ocr_results.append({
                        "psm": psm,
                        "raw_text": text,
                        "cleaned_text": cleaned,
                        "length": len(cleaned)
                    })
                    print(f"  PSM {psm}: '{cleaned}' (len={len(cleaned)})")
                except Exception as e:
                    print(f"  PSM {psm}: ❌ Error - {e}")

            # Find best result
            if ocr_results:
                best_result = max(ocr_results, key=lambda x: x["length"])
                print(f"🏆 Best PSM {best_result['psm']}: '{best_result['cleaned_text']}'")

                results.update({
                    "success": True,
                    "image_shape": image.shape,
                    "preprocessed_shape": processed.shape,
                    "ocr_results": ocr_results,
                    "best_result": best_result
                })
            else:
                print("❌ No OCR results obtained")
                results["error"] = "No OCR results"

        except Exception as e:
            print(f"❌ Error debugging {region_name}: {e}")
            results["error"] = str(e)

        return results

    def debug_capture_comparison(self, regions_dict: dict) -> dict:
        """
        Compare capture quality across multiple regions.

        Args:
            regions_dict: Dictionary of region names to coordinates

        Returns:
            Dictionary with comparison results
        """
        if not self.debug_mode:
            print("[DEBUG] Debug mode not enabled")
            return {}

        print(f"\n{'🔍'} CAPTURE COMPARISON DEBUG")
        print(f"{'─'*50}")

        results = {}

        for region_name, coords in regions_dict.items():
            print(f"\n📍 Testing: {region_name}")
            region_results = self.debug_specific_region(region_name, coords)

            if region_results.get("success", False):
                best_result = region_results.get("best_result", {})
                print(f"   ✅ Success: '{best_result.get('cleaned_text', '')}' (PSM {best_result.get('psm', 'N/A')})")
                results[region_name] = region_results
            else:
                print(f"   ❌ Failed: {region_results.get('error', 'Unknown error')}")
                results[region_name] = region_results

        # Summary
        successful_regions = sum(1 for r in results.values() if r.get("success", False))
        print(f"\n📊 Summary: {successful_regions}/{len(results)} regions captured successfully")

        return results

