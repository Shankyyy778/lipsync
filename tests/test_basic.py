"""
Basic tests that don't require external dependencies.
Tests the core structure and imports.
"""

import unittest
import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestProjectStructure(unittest.TestCase):
    """Test that the project structure is correct."""
    
    def test_project_directories_exist(self):
        """Test that all required directories exist."""
        base_dir = Path(__file__).parent.parent
        
        required_dirs = [
            "app",
            "models", 
            "outputs",
            "samples",
            "scripts",
            "tests"
        ]
        
        for dir_name in required_dirs:
            dir_path = base_dir / dir_name
            self.assertTrue(dir_path.exists(), f"Directory {dir_name} should exist")
    
    def test_app_files_exist(self):
        """Test that all app files exist."""
        base_dir = Path(__file__).parent.parent
        
        required_files = [
            "app/__init__.py",
            "app/streamlit_app.py",
            "app/inference.py", 
            "app/utils.py",
            "requirements.txt",
            "README.md",
            ".gitignore"
        ]
        
        for file_name in required_files:
            file_path = base_dir / file_name
            self.assertTrue(file_path.exists(), f"File {file_name} should exist")
    
    def test_requirements_file_content(self):
        """Test that requirements.txt has expected content."""
        base_dir = Path(__file__).parent.parent
        requirements_path = base_dir / "requirements.txt"
        
        self.assertTrue(requirements_path.exists())
        
        with open(requirements_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for key dependencies
        expected_deps = [
            "streamlit",
            "torch",
            "opencv-python",
            "moviepy",
            "librosa",
            "soundfile",
            "numpy"
        ]
        
        for dep in expected_deps:
            self.assertIn(dep, content, f"Requirements should include {dep}")


class TestAppImports(unittest.TestCase):
    """Test that app modules can be imported (without dependencies)."""
    
    def test_app_init_import(self):
        """Test that app/__init__.py can be imported."""
        try:
            import app
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import app module: {e}")
    
    def test_streamlit_app_structure(self):
        """Test that streamlit_app.py has expected structure."""
        base_dir = Path(__file__).parent.parent
        app_path = base_dir / "app" / "streamlit_app.py"
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key components
        expected_components = [
            "import streamlit as st",
            "from inference import",
            "from utils import",
            "def main():",
            "st.set_page_config",
            "uploaded_image",
            "uploaded_audio",
            "generate_with_model"
        ]
        
        for component in expected_components:
            self.assertIn(component, content, f"streamlit_app.py should contain {component}")


class TestInferenceStructure(unittest.TestCase):
    """Test that inference.py has expected structure."""
    
    def test_inference_file_structure(self):
        """Test that inference.py has expected classes and functions."""
        base_dir = Path(__file__).parent.parent
        inference_path = base_dir / "app" / "inference.py"
        
        with open(inference_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key components
        expected_components = [
            "class ModelBase",
            "class Wav2LipWrapper",
            "class MuseTalkWrapper", 
            "MODEL_REGISTRY",
            "def generate_with_model",
            "def get_available_models"
        ]
        
        for component in expected_components:
            self.assertIn(component, content, f"inference.py should contain {component}")


class TestUtilsStructure(unittest.TestCase):
    """Test that utils.py has expected structure."""
    
    def test_utils_file_structure(self):
        """Test that utils.py has expected functions."""
        base_dir = Path(__file__).parent.parent
        utils_path = base_dir / "app" / "utils.py"
        
        with open(utils_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key functions
        expected_functions = [
            "def ensure_wav",
            "def add_audio_to_video",
            "def detect_and_crop_face",
            "def validate_inputs"
        ]
        
        for func in expected_functions:
            self.assertIn(func, content, f"utils.py should contain {func}")


def run_basic_tests():
    """Run basic structure tests."""
    print("Running basic structure tests...")
    
    try:
        # Test project structure
        base_dir = Path(__file__).parent.parent
        
        # Check key files exist
        key_files = [
            "app/__init__.py",
            "app/streamlit_app.py", 
            "app/inference.py",
            "app/utils.py",
            "requirements.txt",
            "README.md"
        ]
        
        for file_path in key_files:
            full_path = base_dir / file_path
            if not full_path.exists():
                print(f"Missing file: {file_path}")
                return False
            else:
                print(f"Found: {file_path}")
        
        # Check key directories
        key_dirs = ["app", "models", "outputs", "samples", "scripts", "tests"]
        for dir_name in key_dirs:
            dir_path = base_dir / dir_name
            if not dir_path.exists():
                print(f"Missing directory: {dir_name}")
                return False
            else:
                print(f"Found directory: {dir_name}")
        
        print("Basic structure tests passed!")
        return True
        
    except Exception as e:
        print(f"Basic tests failed: {e}")
        return False


if __name__ == "__main__":
    # Run basic tests first
    if run_basic_tests():
        print("\nRunning full test suite...")
        unittest.main(verbosity=2)
    else:
        print("Skipping full test suite due to basic test failures")
        sys.exit(1)
