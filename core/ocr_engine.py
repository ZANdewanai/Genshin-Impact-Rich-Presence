#!/usr/bin/env python3
"""
OCR Engine Abstraction Layer
Allows switching between different OCR engines without changing main application code
"""
import os
import sys
import time
import numpy as np
from PIL import Image

# Add local packages to path
script_dir = os.path.dirname(os.path.abspath(__file__))
local_site_packages = os.path.join(script_dir, "local_packages", "site-packages")
if local_site_packages not in sys.path:
    sys.path.insert(0, local_site_packages)

class OCREngine:
    """Abstract OCR engine interface"""

    def __init__(self, config=None):
        self.config = config or {}
        self.reader = None
        self.name = "Unknown"
        self.logger = None  # For logging (can be set by wrapper)

    def initialize(self):
        """Initialize the OCR engine"""
        raise NotImplementedError

    def readtext(self, image, **kwargs):
        """Process image and return text detection results"""
        raise NotImplementedError

    def get_size_mb(self):
        """Return approximate size of OCR engine in MB"""
        raise NotImplementedError

class EasyOCREngine(OCREngine):
    """EasyOCR implementation"""

    def __init__(self, config=None):
        super().__init__(config)
        self.name = "EasyOCR"

    def initialize(self):
        """Initialize EasyOCR reader"""
        try:
            import easyocr
            
            # Check GPU preference from multiple sources
            use_gpu = self._get_gpu_preference()
            
            if self.logger:
                self.logger.info(f"Initializing EasyOCR with GPU={use_gpu}")
            else:
                print(f"Initializing EasyOCR with GPU={use_gpu}")
            self.reader = easyocr.Reader(['en'], gpu=use_gpu, **self.config)
            return True
        except ImportError:
            print("EasyOCR not available")
            return False

    def _get_gpu_preference(self) -> bool:
        """Determine GPU preference from multiple sources"""
        # Check config file first
        try:
            from CONFIG import USE_GPU
            if not USE_GPU:
                return False
        except (ImportError, AttributeError):
            return False

        # Check if CUDA is actually available
        try:
            import torch
            if not torch.cuda.is_available():
                return False
        except (ImportError, AttributeError):
            return False

        # Check environment variable for explicit override
        cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '').strip()
        if cuda_visible == '':
            # Not set - use GPU if USE_GPU=True and CUDA available (already checked above)
            return True
        elif cuda_visible == '0':
            return True   # Explicitly enabled (GPU 0)
        else:
            # Any other value means explicit GPU selection or disable
            try:
                # Try to parse as integer - if valid, use that GPU
                int(cuda_visible)
                return True
            except ValueError:
                return False

        return True

    def readtext(self, image, **kwargs):
        """Process image with EasyOCR"""
        if self.reader is None:
            if not self.initialize():
                return []
        return self.reader.readtext(image, **kwargs)

    def get_size_mb(self):
        """Return EasyOCR size estimate"""
        return 400  # Approximate size in MB

# Removed PaddleOCR and Tesseract engines - they don't work for game text detection

def get_available_engines():
    """Get list of available OCR engines"""
    engines = []

    # Test EasyOCR
    easyocr_engine = EasyOCREngine()
    if easyocr_engine.initialize():
        engines.append(easyocr_engine)

    return engines

def get_ocr_engine(preferred_engine="auto"):
    """Get OCR engine by preference or auto-select best available"""

    if preferred_engine == "auto":
        # Auto-select: prefer smaller, faster engines first
        available = get_available_engines()

        if not available:
            raise ImportError("No OCR engines available")

        # Sort by size (smaller first) then by speed preference
        # For now, just return the first available
        return available[0]

    elif preferred_engine.lower() == "easyocr":
        engine = EasyOCREngine()
        if engine.initialize():
            return engine
        else:
            raise ImportError("EasyOCR not available")

    else:
        raise ValueError(f"Unknown OCR engine: {preferred_engine}. Only 'easyocr' is supported.")

# Configuration - can be set via environment variable or CONFIG.py
try:
    from CONFIG import OCR_ENGINE
    PREFERRED_OCR_ENGINE = OCR_ENGINE
except ImportError:
    PREFERRED_OCR_ENGINE = os.environ.get("GENSHIN_OCR_ENGINE", "auto")

# Global OCR engine instance (EasyOCR only)
_ocr_engine = None

def get_ocr_reader():
    """Get or create EasyOCR reader instance"""
    global _ocr_engine

    if _ocr_engine is None:
        print("Initializing EasyOCR engine...")
        _ocr_engine = get_ocr_engine("easyocr")
        print(f"Using OCR: {_ocr_engine.name} (~{_ocr_engine.get_size_mb()}MB)")

    return _ocr_engine

def ocr_readtext(image, **kwargs):
    """Drop-in replacement for easyocr.Reader.readtext()"""
    reader = get_ocr_reader()
    return reader.readtext(image, **kwargs)

# For backward compatibility - expose as easyocr-like interface
class Reader:
    """EasyOCR-like Reader class for backward compatibility"""

    def __init__(self, languages=None, gpu=False, **kwargs):
        self.engine = get_ocr_reader()

    def readtext(self, image, **kwargs):
        return self.engine.readtext(image, **kwargs)

if __name__ == "__main__":
    # Test the OCR engines
    print("Testing Available OCR Engines...")

    available_engines = get_available_engines()

    if available_engines:
        print(f"Found {len(available_engines)} OCR engines:")
        for engine in available_engines:
            print(f"   • {engine.name} (~{engine.get_size_mb()}MB)")
    else:
        print("No OCR engines available")

    print("\nTo use in main.py:")
    print("   import ocr_engine")
    print("   reader = ocr_engine.Reader(['en'])")
    print("   results = reader.readtext(image)")
    print("\nEasyOCR is the only supported engine.")
