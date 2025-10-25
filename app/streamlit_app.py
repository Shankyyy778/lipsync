"""
Streamlit web app for lip-sync generation.
Main UI for uploading images/audio and generating lip-synced videos.
"""

import streamlit as st
import os
import tempfile
import time
from pathlib import Path
import logging

# Import our modules
from inference import generate_with_model, get_available_models, check_model_status
from utils import ensure_wav, add_audio_to_video, validate_inputs, detect_and_crop_face

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="🎤 Narris Lip-Sync Demo",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .model-card {
        border: 1px solid #4a5568;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #2d3748;
        color: #e2e8f0;
    }
    .model-card h4 {
        color: #f7fafc;
        margin-bottom: 0.5rem;
    }
    .model-card p {
        color: #cbd5e0;
        margin: 0.25rem 0;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">🎤 Narris Lip-Sync Demo</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: #666;">
            Generate realistic lip-synced videos from static face images and audio files
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for model information
    with st.sidebar:
        st.header("📋 Model Information")
        
        # Get available models
        available_models = get_available_models()
        
        # Model information display
        model_info = {
            'wav2lip': {
                'name': 'Wav2Lip',
                'description': 'Fast and accurate lip-sync',
                'cpu_friendly': '✓',
                'quality': 'High',
                'speed': 'Fast'
            },
            'musetalk': {
                'name': 'MuseTalk',
                'description': 'High-quality diffusion-based',
                'cpu_friendly': '⚠️',
                'quality': 'Very High',
                'speed': 'Slow'
            },
            'speech2lip': {
                'name': 'Speech2Lip',
                'description': '3DMM-based lip motion',
                'cpu_friendly': '✓',
                'quality': 'Medium-High',
                'speed': 'Medium'
            },
            'styletalk': {
                'name': 'StyleTalk',
                'description': 'Stylized talking heads',
                'cpu_friendly': '✓',
                'quality': 'High',
                'speed': 'Medium-Slow'
            }
        }
        
        for model_name, info in available_models.items():
            status = "✅ Available" if info['available'] else "❌ Not Available"
            model_data = model_info.get(model_name, {})
            st.markdown(f"""
            <div class="model-card">
                <h4>{model_data.get('name', model_name.upper())}</h4>
                <p><strong>Status:</strong> {status}</p>
                <p><strong>Description:</strong> {model_data.get('description', 'N/A')}</p>
                <p><strong>CPU Friendly:</strong> {model_data.get('cpu_friendly', 'N/A')}</p>
                <p><strong>Quality:</strong> {model_data.get('quality', 'N/A')}</p>
                <p><strong>Speed:</strong> {model_data.get('speed', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📁 Output Directory")
        st.text(f"Videos saved to: {os.path.abspath('outputs')}")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Upload Files")
        
        # File uploaders
        uploaded_image = st.file_uploader(
            "Upload Face Image",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear face image (JPG, PNG)"
        )
        
        uploaded_audio = st.file_uploader(
            "Upload Audio File",
            type=['wav', 'mp3'],
            help="Upload an audio file (WAV, MP3)"
        )
        
        # Model selection
        st.header("🤖 Select Model")
        model_choice = st.selectbox(
            "Choose Lip-Sync Model",
            options=list(available_models.keys()),
            help="Select the model to use for lip-sync generation"
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            crop_face = st.checkbox(
                "Auto-crop face",
                value=True,
                help="Automatically detect and crop face from image"
            )
            
            # Quality controls for CPU-optimized models
            if model_choice in ['speech2lip', 'styletalk']:
                st.markdown("### ⚙️ Performance Settings")
                
                # Resolution slider
                quality = st.slider(
                    "Output Resolution",
                    min_value=64,
                    max_value=256,
                    value=128,
                    step=32,
                    help="Lower = faster on CPU, Higher = better quality"
                )
                
                # FPS slider
                fps = st.slider(
                    "Frames Per Second",
                    min_value=10,
                    max_value=25,
                    value=15,
                    step=5,
                    help="Lower = faster processing, Higher = smoother video"
                )
                
                # Style control for StyleTalk
                if model_choice == 'styletalk':
                    style_strength = st.slider(
                        "Style Strength",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.5,
                        step=0.1,
                        help="Control stylization intensity"
                    )
                
                # CPU performance warning
                st.info(f"💡 CPU Mode: {quality}x{quality} @ {fps} FPS")
                estimated_time = (quality / 128) * (fps / 15) * 30  # Rough estimate
                st.caption(f"Estimated processing time: ~{estimated_time:.0f}s for 5s video")
            
            elif model_choice == 'wav2lip':
                resize_factor = st.slider(
                    "Quality Factor",
                    min_value=0.5,
                    max_value=2.0,
                    value=1.0,
                    step=0.1,
                    help="Higher values = better quality but slower processing (Wav2Lip only)"
                )
    
    with col2:
        st.header("🎬 Generate Video")
        
        # Generate button
        if st.button("🚀 Generate Lip-Sync Video", type="primary", use_container_width=True):
            if not uploaded_image or not uploaded_audio:
                st.error("Please upload both an image and audio file.")
            else:
                try:
                    # Create temporary directory for processing
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_dir = Path(temp_dir)
                        
                        # Save uploaded files
                        image_path = temp_dir / "input_image.jpg"
                        audio_path = temp_dir / "input_audio.wav"
                        
                        with open(image_path, "wb") as f:
                            f.write(uploaded_image.read())
                        
                        with open(audio_path, "wb") as f:
                            f.write(uploaded_audio.read())
                        
                        # Validate inputs
                        is_valid, error_msg = validate_inputs(str(image_path), str(audio_path))
                        if not is_valid:
                            st.error(f"Input validation failed: {error_msg}")
                            return
                        
                        # Process image (face cropping if enabled)
                        processed_image_path = image_path
                        if crop_face:
                            try:
                                processed_image_path = temp_dir / "processed_image.jpg"
                                detect_and_crop_face(str(image_path), str(processed_image_path))
                                st.info("✅ Face detected and cropped")
                            except Exception as e:
                                st.warning(f"Face detection failed, using original image: {e}")
                                processed_image_path = image_path
                        
                        # Process audio (convert to WAV, 16kHz)
                        processed_audio_path = temp_dir / "processed_audio.wav"
                        ensure_wav(str(audio_path), str(processed_audio_path), sample_rate=16000)
                        st.info("✅ Audio processed (converted to WAV, 16kHz)")
                        
                        # Generate video
                        raw_video_path = temp_dir / "raw_output.mp4"
                        final_video_path = temp_dir / "final_output.mp4"
                        
                        with st.spinner(f"🎬 Generating lip-sync video with {model_choice.upper()}..."):
                            # Prepare kwargs based on model
                            kwargs = {}
                            if model_choice in ['speech2lip', 'styletalk']:
                                kwargs['quality'] = quality
                                kwargs['fps'] = fps
                                if model_choice == 'styletalk':
                                    kwargs['style_strength'] = style_strength
                            elif model_choice == 'wav2lip':
                                kwargs['resize_factor'] = resize_factor
                            
                            # Generate lip-sync video
                            generate_with_model(
                                model_choice,
                                str(processed_image_path),
                                str(processed_audio_path),
                                str(raw_video_path),
                                **kwargs
                            )
                            
                            # Merge audio with video
                            add_audio_to_video(
                                str(raw_video_path),
                                str(processed_audio_path),
                                str(final_video_path)
                            )
                        
                        # Save to outputs directory
                        output_filename = f"lip_sync_{model_choice}_{int(time.time())}.mp4"
                        output_path = Path("outputs") / output_filename
                        
                        # Copy final video to outputs directory
                        import shutil
                        shutil.copy2(str(final_video_path), str(output_path))
                        
                        st.success("✅ Lip-sync video generated successfully!")
                        
                        # Display video
                        st.header("🎥 Generated Video")
                        st.video(str(output_path))
                        
                        # Download button
                        with open(str(output_path), "rb") as f:
                            st.download_button(
                                label="📥 Download Video",
                                data=f.read(),
                                file_name=output_filename,
                                mime="video/mp4",
                                use_container_width=True
                            )
                        
                        # Show file info
                        file_size = os.path.getsize(str(output_path)) / (1024 * 1024)  # MB
                        st.info(f"📊 File size: {file_size:.2f} MB")
                
                except Exception as e:
                    st.error(f"❌ Error generating video: {str(e)}")
                    logger.error(f"Generation error: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>🎤 Narris Lip-Sync Demo | Built with Streamlit</p>
        <p><small>Use responsibly - ensure you have consent for any facial data used</small></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
