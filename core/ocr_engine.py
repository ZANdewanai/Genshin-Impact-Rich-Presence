#!/usr/bin/env python3
"""
OCR Engine - RapidOCR wrapper for Genshin Impact Rich Presence
Lightweight OCR engine built on RapidOCR (ONNX Runtime)
"""

class Reader:
    """RapidOCR Reader class for Genshin Impact Rich Presence"""

    def __init__(self, languages=None, gpu=False, **kwargs):
        """Initialize RapidOCR reader with GPU-only enforcement"""
        # Store GPU parameter for use in _get_gpu_preference
        self._gpu_param = gpu
        
        # ENFORCE GPU-ONLY: First check if GPU providers are available before initialization
        self._validate_gpu_available()
        
        try:
            from rapidocr_onnxruntime import RapidOCR
             
            # Check GPU preference from multiple sources
            use_gpu = self._get_gpu_preference()
             
            print(f"Initializing RapidOCR with GPU={use_gpu}")
            
            self.reader = RapidOCR(use_gpu=use_gpu, **kwargs)
            self.name = "RapidOCR"
            
            # Log GPU provider information and enforce GPU usage
            self._log_gpu_info()
        except ImportError:
            print("RapidOCR not available")
            raise ImportError("RapidOCR is required but not installed. Install with: pip install rapidocr-onnxruntime")
    
    def _validate_gpu_available(self):
        """Validate that GPU providers are available before initialization"""
        try:
            from onnxruntime import get_available_providers
            providers = get_available_providers()
            
            gpu_providers = ["DmlExecutionProvider", "CUDAExecutionProvider"]
            has_gpu = any(provider in providers for provider in gpu_providers)
            
            if not has_gpu:
                raise RuntimeError(
                    "GPU ACCELERATION REQUIRED BUT NOT AVAILABLE!\n"
                    f"Available providers: {providers}\n"
                    "Required providers: DmlExecutionProvider or CUDAExecutionProvider\n"
                    "Please install onnxruntime-directml for Windows GPU support."
                )
            
            # Remove CPU from available providers to enforce GPU-only
            gpu_only_providers = [p for p in providers if p in gpu_providers]
            print(f"[GPU VALIDATION PASSED] GPU-only mode enabled with providers: {gpu_only_providers}")
            
            # Store GPU-only providers for later use
            self._gpu_only_providers = gpu_only_providers
            
        except Exception as e:
            raise RuntimeError(f"GPU validation failed: {e}")

    def _get_gpu_preference(self) -> bool:
        """Determine GPU preference from multiple sources"""
        # Check explicit gpu parameter first (highest priority)
        if hasattr(self, '_gpu_param'):
            return self._gpu_param
            
        # Force GPU usage - no fallback to config
        # User explicitly stated they will NEVER use this app without GPU
        return True

    def _log_gpu_info(self):
        """Log GPU provider information for diagnostics and enforce GPU-only operation"""
        try:
            from onnxruntime import get_available_providers, get_device
            providers = get_available_providers()
            device = get_device()
            
            print(f"Available ONNX Runtime providers: {providers}")
            print(f"Current device: {device}")
            
            # ENFORCE GPU-ONLY: Check if GPU providers are available
            gpu_providers = ["DmlExecutionProvider", "CUDAExecutionProvider"]
            has_gpu = any(provider in providers for provider in gpu_providers)
            
            if not has_gpu:
                raise RuntimeError(
                    "NO GPU PROVIDERS AVAILABLE! "
                    "This application requires GPU acceleration. "
                    f"Available providers: {providers}. "
                    "Please install onnxruntime-directml or onnxruntime-gpu."
                )
            
            # Try to get actual session providers if reader is initialized
            if hasattr(self.reader, 'text_det') and hasattr(self.reader.text_det, 'session'):
                det_providers = self.reader.text_det.session.had_providers
                print(f"Detection session had providers: {det_providers}")
                
                # ENFORCE GPU-ONLY: Check if detection is using GPU
                if not any(provider in det_providers for provider in gpu_providers):
                    raise RuntimeError(
                        "DETECTION IS NOT USING GPU! "
                        f"Detection providers: {det_providers}. "
                        "GPU acceleration is required."
                    )
                
            if hasattr(self.reader, 'text_rec') and hasattr(self.reader.text_rec, 'session'):
                rec_providers = self.reader.text_rec.session.had_providers
                print(f"Recognition session had providers: {rec_providers}")
                
                # ENFORCE GPU-ONLY: Check if recognition is using GPU
                if not any(provider in rec_providers for provider in gpu_providers):
                    raise RuntimeError(
                        "RECOGNITION IS NOT USING GPU! "
                        f"Recognition providers: {rec_providers}. "
                        "GPU acceleration is required."
                    )
                
            print("[SUCCESS] GPU acceleration is properly configured and active")
                
        except Exception as e:
            print(f"[CRITICAL] GPU validation failed: {e}")
            raise

    def readtext(self, image, allowlist=None, wait=True, **kwargs):
        """
        Process image with RapidOCR
        
        RapidOCR returns: ( [[bbox, text, confidence_string], ...], [timing_info] )
        Standard result format: [(bbox, text, confidence_float), ...]
        
        When ``wait`` is False the call does NOT queue behind other OCR users:
        it acquires the shared OCR lock with a short timeout and raises
        TimeoutError instead of blocking. Low-priority/high-frequency consumers
        (LocationSensor) use this so a long CharSensor fallback sweep can't
        starve location updates - they simply retry on their next tick.
        
        RapidOCR output is converted into this standard format.
        """
        if self.reader is None:
            raise RuntimeError("RapidOCR reader not initialized")
        
        from core.state import ocr_lock
        if wait:
            with ocr_lock:
                result_tuple = self.reader(image)
        else:
            # Non-blocking path: short-timeout acquire, ALWAYS paired with a
            # release. (A previous version acquired here without releasing -
            # every successful non-wait read then deadlocked all other
            # sensors on the shared OCR lock forever.)
            if not ocr_lock.acquire(timeout=0.05):
                raise TimeoutError("OCR engine busy")
            try:
                result_tuple = self.reader(image)
            finally:
                ocr_lock.release()
            
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
        reader = Reader(['en'], gpu=True)
        print(f"Successfully initialized: {reader.name} (~{reader.get_size_mb()}MB)")
        print("\nTo use in main.py:")
        print("   from core import ocr_engine")
        print("   reader = ocr_engine.Reader(['en'], gpu=True)")
        print("   results = reader.readtext(image)")
    except ImportError as e:
        print(f"Failed to initialize: {e}")
