"""
Demo script for the Lip-Sync Web App.
This script provides a quick way to test the application without the web interface.
"""

import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_installation():
    """Check if the app is properly installed."""
    print("Checking installation...")
    
    # Check if app modules exist
    try:
        from app import inference, utils
        print("App modules imported successfully")
    except ImportError as e:
        print(f"Failed to import app modules: {e}")
        return False
    
    # Check if models directory exists
    models_dir = Path("models")
    if not models_dir.exists():
        print("Models directory not found. Run 'bash scripts/download_weights.sh' for setup instructions.")
        return False
    
    print("Installation check passed!")
    return True

def check_models():
    """Check which models are available."""
    print("\nChecking model availability...")
    
    try:
        from app.inference import get_available_models, check_model_status
        
        models = get_available_models()
        print(f"Found {len(models)} models: {list(models.keys())}")
        
        for model_name, info in models.items():
            status = "Available" if info['available'] else "Not Available"
            print(f"  {model_name.upper()}: {status}")
            
            if not info['available']:
                print(f"    Path: {info['base_dir']}")
                print(f"    Note: Download model files to make this model available")
        
        return True
        
    except Exception as e:
        print(f"Error checking models: {e}")
        return False

def show_usage():
    """Show usage instructions."""
    print("\nUsage Instructions:")
    print("=" * 50)
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("2. Setup models (follow instructions in scripts/download_weights.sh):")
    print("   bash scripts/download_weights.sh")
    print()
    print("3. Run the web app:")
    print("   streamlit run app/streamlit_app.py")
    print()
    print("4. Open your browser to: http://localhost:8501")
    print()
    print("5. Upload a face image and audio file, then generate lip-sync video!")

def main():
    """Main demo function."""
    print("Narris Lip-Sync Web App - Demo")
    print("=" * 40)
    
    # Check installation
    if not check_installation():
        print("\nInstallation check failed. Please check your setup.")
        return
    
    # Check models
    if not check_models():
        print("\nModel check failed.")
        return
    
    # Show usage
    show_usage()
    
    print("\nDemo completed successfully!")
    print("Ready to run: streamlit run app/streamlit_app.py")

if __name__ == "__main__":
    main()
