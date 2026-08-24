#!/usr/bin/env python3
"""
OCR Engine - RapidOCR wrapper for Genshin Impact Rich Presence
Lightweight OCR engine built on RapidOCR (ONNX Runtime)
"""

class Reader:
    """RapidOCR Reader class for Genshin Impact Rich Presence"""

    def __init__(self, languages=None, gpu=False, **kwargs):
        """Initialize RapidOCR reader"""
        try:
            from rapidocr_onnxruntime import RapidOCR
            
            # Check GPU preference from multiple sources
            use_gpu = self._get_gpu_preference()
            
            print(f"Initializing RapidOCR with GPU={use_gpu}")
            self.reader = RapidOCR(use_gpu=use_gpu, **kwargs)
            self.name = "RapidOCR"
        except ImportError:
            print("RapidOCR not available")
            raise ImportError("RapidOCR is required but not installed. Install with: pip install rapidocr-onnxruntime")

    def _get_gpu_preference(self) -> bool:
        """Determine GPU preference from multiple sources"""
        # Check config file first
        try:
            from CONFIG import USE_GPU
            if not USE_GPU:
                return False
        except (ImportError, AttributeError):
            return False

        # RapidOCR uses ONNX Runtime which supports DirectML on Windows
        # No CUDA availability checks are needed with ONNX Runtime
        # Just return True if USE_GPU is True
        return True

    def readtext(self, image, allowlist=None, **kwargs):
        """
        Process image with RapidOCR
        
        RapidOCR returns: ( [[bbox, text, confidence_string], ...], [timing_info] )
        Standard result format: [(bbox, text, confidence_float), ...]
        
        RapidOCR output is converted into this standard format.
        """
        if self.reader is None:
            raise RuntimeError("RapidOCR reader not initialized")
        
        from core.state import ocr_lock
        with ocr_lock:
            result_tuple = self.reader(image)
        
        # Extract the detections (first element of tuple), handle None case
        detections = []
        if result_tuple and len(result_tuple) > 0 and result_tuple[0] is not None:
            detections = result_tuple[0]
        
        # If allowlist is provided, filter results
        if allowlist:
            filtered_result = []
            for item in detections:
                # RapidOCR returns: [bbox, text, confidence_string]
                if item is None or len(item) < 3:
                    continue
                bbox, text, confidence_str = item
                # Ensure text is a string
                if not isinstance(text, str):
                    text = str(text)
                # Filter text to only include characters in allowlist
                filtered_text = ''.join([c for c in text if c in allowlist])
                if filtered_text:  # Only keep if there's something after filtering
                    # Convert confidence string to float
                    try:
                        confidence = float(confidence_str)
                    except (ValueError, TypeError):
                        confidence = 0.0
                    filtered_result.append((bbox, filtered_text, confidence))
            return filtered_result
        
        # Convert RapidOCR output to the standard result format
        formatted_result = []
        for item in detections:
            if item is not None and len(item) >= 3:
                bbox, text, confidence_str = item
                # Ensure text is a string
                if not isinstance(text, str):
                    text = str(text)
                # Convert confidence string to float
                try:
                    confidence = float(confidence_str)
                except (ValueError, TypeError):
                    confidence = 0.0
                formatted_result.append((bbox, text, confidence))
        return formatted_result

    def get_size_mb(self):
        """Return RapidOCR size estimate"""
        return 50  # Approximate in-memory footprint in MB

if __name__ == "__main__":
    # Test the OCR engine
    print("Testing RapidOCR Engine...")

    try:
        reader = Reader(['en'])
        print(f"Successfully initialized: {reader.name} (~{reader.get_size_mb()}MB)")
        print("\nTo use in main.py:")
        print("   from core import ocr_engine")
        print("   reader = ocr_engine.Reader(['en'])")
        print("   results = reader.readtext(image)")
    except ImportError as e:
        print(f"Failed to initialize: {e}")
