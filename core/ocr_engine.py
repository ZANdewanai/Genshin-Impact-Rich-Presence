#!/usr/bin/env python3
"""
OCR Engine - RapidOCR wrapper for Genshin Impact Rich Presence
Lightweight OCR engine built on RapidOCR (ONNX Runtime)
"""

# Suppress ONNX Runtime verbose logging BEFORE importing onnxruntime/rapidocr
import os
os.environ.setdefault("ORT_LOGGING_LEVEL", "ERROR")

class Reader:
    """RapidOCR Reader class for Genshin Impact Rich Presence"""

    def __init__(self, languages=None, gpu=True, **kwargs):
        """Initialize RapidOCR reader with GPU-only enforcement"""
        # GPU is required - no CPU fallback
        self._validate_and_init(gpu, **kwargs)

    def _validate_and_init(self, gpu, **kwargs):
        """Single-pass GPU validation + RapidOCR initialization"""
        try:
            import onnxruntime as ort
            # Suppress ONNX Runtime C++ logger output (must be called before first use)
            try:
                ort.set_default_logger_severity(3)  # 3 = ERROR level
            except AttributeError:
                pass
            from onnxruntime import get_available_providers
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as e:
            raise ImportError("RapidOCR/onnxruntime required. Install: pip install rapidocr-onnxruntime onnxruntime-directml") from e

        # Check GPU providers once
        providers = get_available_providers()
        gpu_providers = ["DmlExecutionProvider", "CUDAExecutionProvider"]
        has_gpu = any(p in providers for p in gpu_providers)

        if not has_gpu:
            raise RuntimeError(
                "GPU ACCELERATION REQUIRED BUT NOT AVAILABLE!\n"
                f"Available providers: {providers}\n"
                "Required: DmlExecutionProvider or CUDAExecutionProvider\n"
                "Install: pip install onnxruntime-directml"
            )

        print(f"[GPU VALIDATION PASSED] GPU-only mode enabled with providers: {[p for p in providers if p in gpu_providers]}")

        # Initialize RapidOCR with GPU
        self.reader = RapidOCR(use_gpu=gpu, **kwargs)
        self.name = "RapidOCR"
        print(f"Initializing RapidOCR with GPU={gpu}")

        # Verify sessions use GPU (post-init check)
        self._verify_gpu_sessions(gpu_providers)

    def _verify_gpu_sessions(self, gpu_providers):
        """Verify detection/recognition sessions use GPU providers"""
        try:
            if hasattr(self.reader, 'text_det') and hasattr(self.reader.text_det, 'session'):
                det_providers = self.reader.text_det.session.had_providers
                print(f"Detection session providers: {det_providers}")
                if not any(p in det_providers for p in gpu_providers):
                    raise RuntimeError(f"DETECTION NOT USING GPU! Providers: {det_providers}")

            if hasattr(self.reader, 'text_rec') and hasattr(self.reader.text_rec, 'session'):
                rec_providers = self.reader.text_rec.session.had_providers
                print(f"Recognition session providers: {rec_providers}")
                if not any(p in rec_providers for p in gpu_providers):
                    raise RuntimeError(f"RECOGNITION NOT USING GPU! Providers: {rec_providers}")

            print("[SUCCESS] GPU acceleration configured and active")
        except Exception as e:
            print(f"[CRITICAL] GPU session verification failed: {e}")
            raise

    def readtext(self, image, allowlist=None, wait=True, **kwargs):
        """
        Process image with RapidOCR.

        RapidOCR returns: ( [[bbox, text, confidence_string], ...], [timing_info] )
        Standard result format: [(bbox, text, confidence_float), ...]

        When ``wait`` is False the call does NOT queue behind other OCR users:
        it acquires the shared OCR lock with a short timeout and raises
        TimeoutError instead of blocking. Low-priority/high-frequency consumers
        (LocationSensor) use this so a long CharSensor fallback sweep can't
        starve location updates - they simply retry on their next tick.
        """
        if self.reader is None:
            raise RuntimeError("RapidOCR reader not initialized")

        from core.state import ocr_lock
        if wait:
            with ocr_lock:
                result_tuple = self.reader(image)
        else:
            # Non-blocking path: short-timeout acquire, ALWAYS paired with release
            if not ocr_lock.acquire(timeout=0.05):
                raise TimeoutError("OCR engine busy")
            try:
                result_tuple = self.reader(image)
            finally:
                ocr_lock.release()

        # Extract detections (first element of tuple), handle None case
        detections = []
        if result_tuple and len(result_tuple) > 0 and result_tuple[0] is not None:
            detections = result_tuple[0]

        # If allowlist provided, filter results
        if allowlist:
            filtered_result = []
            for item in detections:
                if item is None or len(item) < 3:
                    continue
                bbox, text, confidence_str = item
                if not isinstance(text, str):
                    text = str(text)
                filtered_text = ''.join([c for c in text if c in allowlist])
                if filtered_text:
                    try:
                        confidence = float(confidence_str)
                    except (ValueError, TypeError):
                        confidence = 0.0
                    filtered_result.append((bbox, filtered_text, confidence))
            return filtered_result

        # Convert RapidOCR output to standard format
        formatted_result = []
        for item in detections:
            if item is not None and len(item) >= 3:
                bbox, text, confidence_str = item
                if not isinstance(text, str):
                    text = str(text)
                try:
                    confidence = float(confidence_str)
                except (ValueError, TypeError):
                    confidence = 0.0
                formatted_result.append((bbox, text, confidence))
        return formatted_result

    def get_size_mb(self):
        """Return RapidOCR size estimate"""
        return 50  # Approximate in-memory footprint in MB