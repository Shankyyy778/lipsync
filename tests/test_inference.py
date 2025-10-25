"""
Test suite for the lip-sync web app.
Tests model wrappers, utilities, and basic functionality.
"""

import unittest
import os
import tempfile
import numpy as np
from pathlib import Path
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.inference import Wav2LipWrapper, MuseTalkWrapper, get_available_models, check_model_status
from app.utils import ensure_wav, add_audio_to_video, validate_inputs, detect_and_crop_face
import librosa
import soundfile as sf
import cv2


class TestModelWrappers(unittest.TestCase):
    """Test model wrapper classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.temp_dir, "test_image.jpg")
        self.test_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        
        # Create test image
        self.create_test_image()
        
        # Create test audio
        self.create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_image(self):
        """Create a simple test image."""
        # Create a 256x256 RGB image with a simple pattern
        image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        cv2.imwrite(self.test_image_path, image)
    
    def create_test_audio(self):
        """Create a simple test audio file."""
        # Generate 2 seconds of sine wave at 440Hz
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5
        sf.write(self.test_audio_path, audio, sample_rate)
    
    def test_wav2lip_wrapper_initialization(self):
        """Test Wav2Lip wrapper initialization."""
        wrapper = Wav2LipWrapper()
        self.assertEqual(wrapper.name, "wav2lipwrapper")
        self.assertFalse(wrapper.check_model_available())  # Model not downloaded yet
    
    def test_musetalk_wrapper_initialization(self):
        """Test MuseTalk wrapper initialization."""
        wrapper = MuseTalkWrapper()
        self.assertEqual(wrapper.name, "musetalkwrapper")
        self.assertFalse(wrapper.check_model_available())  # Model not downloaded yet
    
    def test_model_registry(self):
        """Test model registry functionality."""
        available_models = get_available_models()
        self.assertIn("wav2lip", available_models)
        self.assertIn("musetalk", available_models)
        
        # Check model status
        wav2lip_status = check_model_status("wav2lip")
        self.assertIn("available", wav2lip_status)
        self.assertFalse(wav2lip_status["available"])  # Not downloaded yet


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_ensure_wav(self):
        """Test audio conversion to WAV format."""
        # Create test audio file
        input_path = os.path.join(self.temp_dir, "input.wav")
        output_path = os.path.join(self.temp_dir, "output.wav")
        
        # Generate test audio
        sample_rate = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)
        sf.write(input_path, audio, sample_rate)
        
        # Convert to 16kHz
        result_path = ensure_wav(input_path, output_path, sample_rate=16000)
        
        # Verify output
        self.assertTrue(os.path.exists(result_path))
        
        # Load and check sample rate
        converted_audio, sr = librosa.load(result_path, sr=None)
        self.assertEqual(sr, 16000)
        self.assertEqual(len(converted_audio), 16000)  # 1 second at 16kHz
    
    def test_validate_inputs(self):
        """Test input validation."""
        # Create test files
        image_path = os.path.join(self.temp_dir, "test.jpg")
        audio_path = os.path.join(self.temp_dir, "test.wav")
        
        # Create test image
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        cv2.imwrite(image_path, image)
        
        # Create test audio
        audio = np.random.randn(16000)  # 1 second at 16kHz
        sf.write(audio_path, audio, 16000)
        
        # Test valid inputs
        is_valid, error_msg = validate_inputs(image_path, audio_path)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "Inputs are valid")
        
        # Test invalid image
        is_valid, error_msg = validate_inputs("nonexistent.jpg", audio_path)
        self.assertFalse(is_valid)
        self.assertIn("not found", error_msg)
        
        # Test invalid audio
        is_valid, error_msg = validate_inputs(image_path, "nonexistent.wav")
        self.assertFalse(is_valid)
        self.assertIn("not found", error_msg)
    
    def test_detect_and_crop_face(self):
        """Test face detection and cropping."""
        # Create a simple test image (no actual face)
        image_path = os.path.join(self.temp_dir, "test_face.jpg")
        output_path = os.path.join(self.temp_dir, "cropped_face.jpg")
        
        # Create test image
        image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        cv2.imwrite(image_path, image)
        
        # Test face detection (should return original if no face found)
        result_path = detect_and_crop_face(image_path, output_path)
        self.assertTrue(os.path.exists(result_path))
    
    def test_add_audio_to_video(self):
        """Test video and audio merging."""
        # This test requires actual video files, so we'll just test the function exists
        # In a real scenario, you'd need to create test video files
        self.assertTrue(callable(add_audio_to_video))


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_import_all_modules(self):
        """Test that all modules can be imported."""
        try:
            from app import inference, utils
            from app.inference import Wav2LipWrapper, MuseTalkWrapper
            from app.utils import ensure_wav, add_audio_to_video
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import modules: {e}")
    
    def test_model_registry_completeness(self):
        """Test that model registry contains expected models."""
        from app.inference import MODEL_REGISTRY
        
        self.assertIn("wav2lip", MODEL_REGISTRY)
        self.assertIn("musetalk", MODEL_REGISTRY)
        
        # Check wrapper types
        self.assertIsInstance(MODEL_REGISTRY["wav2lip"], Wav2LipWrapper)
        self.assertIsInstance(MODEL_REGISTRY["musetalk"], MuseTalkWrapper)


def run_smoke_tests():
    """Run basic smoke tests to verify the app can start."""
    print("🧪 Running smoke tests...")
    
    try:
        # Test imports
        from app.inference import get_available_models, check_model_status
        from app.utils import validate_inputs
        print("✅ All modules imported successfully")
        
        # Test model registry
        models = get_available_models()
        print(f"✅ Found {len(models)} models: {list(models.keys())}")
        
        # Test model status
        for model_name in models.keys():
            status = check_model_status(model_name)
            print(f"✅ {model_name}: {'Available' if status['available'] else 'Not Available'}")
        
        print("✅ Smoke tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Smoke tests failed: {e}")
        return False


if __name__ == "__main__":
    # Run smoke tests first
    if run_smoke_tests():
        print("\n🧪 Running full test suite...")
        unittest.main(verbosity=2)
    else:
        print("❌ Skipping full test suite due to smoke test failures")
        sys.exit(1)
