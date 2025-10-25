"""
Utility functions for audio and video processing in the lip-sync web app.
"""

import os
import librosa
import soundfile as sf
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
import cv2
from typing import Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_wav(input_path: str, output_path: str, sample_rate: int = 16000) -> str:
    """
    Convert audio file to WAV format with specified sample rate.
    
    Args:
        input_path: Path to input audio file
        output_path: Path to save converted WAV file
        sample_rate: Target sample rate (default: 16000 Hz)
    
    Returns:
        Path to the converted WAV file
    """
    try:
        # Load audio file
        audio, sr = librosa.load(input_path, sr=sample_rate)
        
        # Ensure audio is mono
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio)
        
        # Normalize audio
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save as WAV
        sf.write(output_path, audio, sample_rate)
        
        logger.info(f"Audio converted to WAV: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        raise


def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Merge video and audio files into a single video file.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        output_path: Path to save merged video
    
    Returns:
        Path to the merged video file
    """
    try:
        # Load video and audio
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        
        # Ensure audio duration matches video duration
        if audio_clip.duration > video_clip.duration:
            audio_clip = audio_clip.subclip(0, video_clip.duration)
        elif audio_clip.duration < video_clip.duration:
            # Loop audio if it's shorter than video
            loops_needed = int(np.ceil(video_clip.duration / audio_clip.duration))
            audio_clip = audio_clip.loop(loops_needed).subclip(0, video_clip.duration)
        
        # Set audio to video
        final_video = video_clip.set_audio(audio_clip)
        
        # Write the result with high quality settings
        try:
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                bitrate='5000k',  # High bitrate for better quality
                fps=25,  # Match original FPS
                preset='slow',  # Better compression
                ffmpeg_params=['-crf', '18']  # High quality CRF
            )
        except Exception as e:
            logger.warning(f"High quality encoding failed: {e}")
            logger.info("Trying basic encoding...")
            # Fallback to basic encoding
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
        
        # Close clips to free memory
        video_clip.close()
        audio_clip.close()
        final_video.close()
        
        logger.info(f"Video and audio merged: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error merging video and audio: {e}")
        raise


def detect_and_crop_face(image_path: str, output_path: Optional[str] = None) -> str:
    """
    Detect and crop face from image using OpenCV.
    
    Args:
        image_path: Path to input image
        output_path: Path to save cropped face (optional)
    
    Returns:
        Path to the cropped face image
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Load face cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            logger.warning("No face detected, using original image")
            if output_path:
                cv2.imwrite(output_path, image)
                return output_path
            return image_path
        
        # Get the largest face
        largest_face = max(faces, key=lambda x: x[2] * x[3])
        x, y, w, h = largest_face
        
        # Add some padding around the face
        padding = 0.2
        x_pad = int(w * padding)
        y_pad = int(h * padding)
        
        x_start = max(0, x - x_pad)
        y_start = max(0, y - y_pad)
        x_end = min(image.shape[1], x + w + x_pad)
        y_end = min(image.shape[0], y + h + y_pad)
        
        # Crop the face
        cropped_face = image[y_start:y_end, x_start:x_end]
        
        # Save cropped face
        if output_path:
            cv2.imwrite(output_path, cropped_face)
            logger.info(f"Face cropped and saved: {output_path}")
            return output_path
        else:
            # Save to same directory with _face suffix
            base_name = os.path.splitext(image_path)[0]
            ext = os.path.splitext(image_path)[1]
            output_path = f"{base_name}_face{ext}"
            cv2.imwrite(output_path, cropped_face)
            logger.info(f"Face cropped and saved: {output_path}")
            return output_path
        
    except Exception as e:
        logger.error(f"Error detecting/cropping face: {e}")
        # Return original image path if face detection fails
        return image_path


def get_video_info(video_path: str) -> dict:
    """
    Get basic information about a video file.
    
    Args:
        video_path: Path to video file
    
    Returns:
        Dictionary with video information
    """
    try:
        clip = VideoFileClip(video_path)
        info = {
            'duration': clip.duration,
            'fps': clip.fps,
            'size': clip.size,
            'has_audio': clip.audio is not None
        }
        clip.close()
        return info
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return {}


def validate_inputs(image_path: str, audio_path: str) -> Tuple[bool, str]:
    """
    Validate input image and audio files.
    
    Args:
        image_path: Path to image file
        audio_path: Path to audio file
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if files exist
        if not os.path.exists(image_path):
            return False, f"Image file not found: {image_path}"
        
        if not os.path.exists(audio_path):
            return False, f"Audio file not found: {audio_path}"
        
        # Check image format
        image_ext = os.path.splitext(image_path)[1].lower()
        if image_ext not in ['.jpg', '.jpeg', '.png']:
            return False, f"Unsupported image format: {image_ext}"
        
        # Check audio format
        audio_ext = os.path.splitext(audio_path)[1].lower()
        if audio_ext not in ['.wav', '.mp3', '.m4a']:
            return False, f"Unsupported audio format: {audio_ext}"
        
        # Try to load image
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False, "Invalid image file"
        except:
            return False, "Error reading image file"
        
        # Try to load audio
        try:
            audio, sr = librosa.load(audio_path, sr=None)
            if len(audio) == 0:
                return False, "Empty audio file"
        except:
            return False, "Error reading audio file"
        
        return True, "Inputs are valid"
        
    except Exception as e:
        return False, f"Validation error: {e}"


def detect_face_with_fallback(image_path: str, method: str = 'auto'):
    """
    Detect face with multiple fallback methods.
    
    Args:
        image_path: Path to input image
        method: 'auto', 'mediapipe', 'dlib', 'sfd'
    
    Returns:
        Face bounding box and landmarks
    """
    import cv2
    
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    # Try methods in order
    methods = ['mediapipe', 'sfd', 'dlib'] if method == 'auto' else [method]
    
    for method_name in methods:
        try:
            logger.info(f"Trying face detection with: {method_name}")
            
            if method_name == 'mediapipe':
                # Use MediaPipe (lightweight)
                import mediapipe as mp
                mp_face_detection = mp.solutions.face_detection
                face_detection = mp_face_detection.FaceDetection(
                    min_detection_confidence=0.5
                )
                results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                if results.detections:
                    detection = results.detections[0]
                    bbox = detection.location_data.relative_bounding_box
                    h, w = image.shape[:2]
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    logger.info(f"Face detected with {method_name}")
                    return (x, y, width, height), method_name
            
            elif method_name == 'sfd':
                # Use S3FD from Wav2Lip
                from face_detection import FaceAlignment, LandmarksType
                fa = FaceAlignment(LandmarksType._2D, device='cpu')
                faces = fa.get_detections_for_batch([image])
                if faces and faces[0] is not None:
                    logger.info(f"Face detected with {method_name}")
                    return faces[0], method_name
            
            elif method_name == 'dlib':
                # Use dlib if available
                try:
                    import dlib
                    detector = dlib.get_frontal_face_detector()
                    faces = detector(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
                    if len(faces) > 0:
                        face = faces[0]
                        bbox = (face.left(), face.top(), face.width(), face.height())
                        logger.info(f"Face detected with {method_name}")
                        return bbox, method_name
                except ImportError:
                    logger.warning("dlib not available, skipping")
                    continue
        
        except Exception as e:
            logger.warning(f"Face detection with {method_name} failed: {e}")
            continue
    
    raise RuntimeError("All face detection methods failed")
