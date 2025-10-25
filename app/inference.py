"""
Model inference framework for lip-sync generation.
Supports Wav2Lip and MuseTalk models with unified interface.
"""

import os
import sys
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import tempfile
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelBase(ABC):
    """Abstract base class for lip-sync models."""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.name = self.__class__.__name__.replace('Wrapper', '').lower()
    
    @abstractmethod
    def generate(self, image_path: str, audio_path: str, output_path: str, **kwargs) -> str:
        """
        Generate lip-synced video from image and audio.
        
        Args:
            image_path: Path to input face image
            audio_path: Path to input audio file
            output_path: Path to save output video
            **kwargs: Additional model-specific parameters
        
        Returns:
            Path to generated video
        """
        pass
    
    def check_model_available(self) -> bool:
        """Check if model files are available."""
        return os.path.exists(self.base_dir)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'name': self.name,
            'base_dir': self.base_dir,
            'available': self.check_model_available()
        }


class Wav2LipWrapper(ModelBase):
    """Wrapper for Wav2Lip model."""
    
    def __init__(self, base_dir: str = "models/wav2lip"):
        super().__init__(base_dir)
        self.checkpoint_path = os.path.abspath(os.path.join(base_dir, "checkpoints", "wav2lip_gan.pth"))
        self.inference_script = os.path.abspath(os.path.join(base_dir, "inference.py"))
    
    def generate(self, image_path: str, audio_path: str, output_path: str, **kwargs) -> str:
        """Generate lip-sync video using Wav2Lip."""
        try:
            # Check if model is available
            if not self.check_model_available():
                raise FileNotFoundError(f"Wav2Lip model not found at {self.base_dir}")
            
            if not os.path.exists(self.checkpoint_path):
                raise FileNotFoundError(f"Wav2Lip checkpoint not found at {self.checkpoint_path}")
            
            if not os.path.exists(self.inference_script):
                raise FileNotFoundError(f"Wav2Lip inference script not found at {self.inference_script}")
            
            # Prepare command with absolute paths
            cmd = [
                sys.executable, self.inference_script,
                "--checkpoint_path", self.checkpoint_path,
                "--face", os.path.abspath(image_path),
                "--audio", os.path.abspath(audio_path),
                "--outfile", os.path.abspath(output_path)
            ]
            
            # Add optional parameters
            if 'resize_factor' in kwargs:
                # Convert float to int for Wav2Lip
                resize_factor = int(float(kwargs['resize_factor']))
                cmd.extend(["--resize_factor", str(resize_factor)])
            
            logger.info(f"Running Wav2Lip with command: {' '.join(cmd)}")
            
            # Run inference with environment variables
            env = os.environ.copy()
            env['PYTHONPATH'] = os.pathsep.join(sys.path)
            
            result = subprocess.run(
                cmd,
                cwd=os.path.abspath(self.base_dir),
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not os.path.exists(output_path):
                raise RuntimeError("Wav2Lip did not generate output file")
            
            logger.info(f"Wav2Lip generation completed: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Wav2Lip subprocess error: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise RuntimeError(f"Wav2Lip inference failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Wav2Lip error: {e}")
            raise


class MuseTalkWrapper(ModelBase):
    """Wrapper for MuseTalk model."""
    
    def __init__(self, base_dir: str = "models/musetalk"):
        super().__init__(base_dir)
        self.checkpoint_path = os.path.abspath(os.path.join(base_dir, "models", "musetalk", "pytorch_model.bin"))
        self.config_path = os.path.abspath(os.path.join(base_dir, "configs", "inference", "test.yaml"))
        self.inference_script = os.path.abspath(os.path.join(base_dir, "scripts", "inference.py"))
    
    def generate(self, image_path: str, audio_path: str, output_path: str, **kwargs) -> str:
        """Generate lip-sync video using MuseTalk."""
        try:
            # Check if model is available
            if not self.check_model_available():
                raise FileNotFoundError(f"MuseTalk model not found at {self.base_dir}")
            
            if not os.path.exists(self.checkpoint_path):
                raise FileNotFoundError(f"MuseTalk checkpoint not found at {self.checkpoint_path}")
            
            if not os.path.exists(self.inference_script):
                raise FileNotFoundError(f"MuseTalk inference script not found at {self.inference_script}")
            
            # Create a temporary config file for this specific task
            import tempfile
            import yaml
            
            # Create temp config file
            temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
            config_data = {
                'task_0': {
                    'video_path': os.path.abspath(image_path),
                    'audio_path': os.path.abspath(audio_path),
                    'output_path': os.path.abspath(output_path)
                }
            }
            yaml.dump(config_data, temp_config)
            temp_config.close()
            
            # Prepare command for MuseTalk with correct model paths
            # MuseTalk script runs from models/musetalk directory, so paths are relative to that
            cmd = [
                sys.executable, self.inference_script,
                "--inference_config", temp_config.name,
                "--result_dir", os.path.dirname(os.path.abspath(output_path)),
                "--output_vid_name", os.path.basename(output_path),
                "--unet_config", "models/musetalk/musetalk.json",
                "--unet_model_path", "models/musetalkV15/unet.pth",
                "--whisper_dir", "models/whisper",
                "--vae_type", "sd-vae"
            ]
            
            # Add optional parameters
            if 'device' in kwargs:
                cmd.extend(["--device", kwargs['device']])
            
            logger.info(f"Running MuseTalk with command: {' '.join(cmd)}")
            
            # Run inference with environment variables
            env = os.environ.copy()
            # Add current Python path plus MuseTalk directory
            python_paths = sys.path + [os.path.abspath(self.base_dir)]
            env['PYTHONPATH'] = os.pathsep.join(python_paths)
            
            result = subprocess.run(
                cmd,
                cwd=os.path.abspath(self.base_dir),
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Clean up temporary config file
            try:
                os.unlink(temp_config.name)
            except:
                pass
            
            if not os.path.exists(output_path):
                raise RuntimeError("MuseTalk did not generate output file")
            
            logger.info(f"MuseTalk generation completed: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"MuseTalk subprocess error: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise RuntimeError(f"MuseTalk inference failed: {e.stderr}")
        except Exception as e:
            logger.error(f"MuseTalk error: {e}")
            raise


class Speech2LipWrapper(ModelBase):
    """Wrapper for Speech2Lip model."""
    
    def __init__(self, base_dir: str = "models/speech2lip"):
        super().__init__(base_dir)
        self.checkpoint_path = os.path.join(base_dir, "checkpoints")
        self.inference_script = os.path.abspath(os.path.join(base_dir, "simple_inference.py"))
        
    def generate(self, image_path: str, audio_path: str, output_path: str, **kwargs) -> str:
        """Generate lip-synced video using Speech2Lip."""
        try:
            # Extract parameters
            quality = kwargs.get('quality', 128)  # 128x128 default for CPU
            fps = kwargs.get('fps', 15)  # 15 FPS default for CPU
            
            # Build command
            cmd = [
                sys.executable, self.inference_script,
                "--image", os.path.abspath(image_path),
                "--audio", os.path.abspath(audio_path),
                "--output", os.path.abspath(output_path),
                "--resolution", str(quality),
                "--fps", str(fps),
                "--device", "cpu"
            ]
            
            # Set environment
            env = os.environ.copy()
            env['PYTHONPATH'] = os.pathsep.join([self.base_dir] + sys.path)
            
            # Run inference
            result = subprocess.run(
                cmd,
                cwd=os.path.abspath("."),  # Use project root directory
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not os.path.exists(output_path):
                raise RuntimeError("Speech2Lip did not generate output")
            
            logger.info(f"Speech2Lip generation completed: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Speech2Lip error: {e.stderr}")
            raise RuntimeError(f"Speech2Lip inference failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Speech2Lip error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            'name': 'speech2lip',
            'display_name': 'Speech2Lip',
            'description': 'Audio-driven lip motion with 3DMM tracking',
            'cpu_friendly': True,
            'quality_range': (64, 256),
            'fps_range': (10, 25),
            'default_quality': 128,
            'default_fps': 15
        }


class StyleTalkWrapper(ModelBase):
    """Wrapper for StyleTalk model."""
    
    def __init__(self, base_dir: str = "models/styletalk"):
        super().__init__(base_dir)
        self.checkpoint_path = os.path.join(base_dir, "checkpoints")
        self.inference_script = os.path.abspath(os.path.join(base_dir, "cpu_inference.py"))
        
    def generate(self, image_path: str, audio_path: str, output_path: str, **kwargs) -> str:
        """Generate stylized talking head using StyleTalk."""
        try:
            # Extract parameters
            quality = kwargs.get('quality', 256)  # 256x256 default for StyleTalk
            fps = kwargs.get('fps', 25)  # 25 FPS default for StyleTalk
            style_strength = kwargs.get('style_strength', 0.5)  # Style control
            
            # Build command for StyleTalk CPU inference
            cmd = [
                sys.executable, self.inference_script,
                "--image", os.path.abspath(image_path),
                "--audio", os.path.abspath(audio_path),
                "--output", os.path.abspath(output_path),
                "--resolution", str(quality),
                "--fps", str(fps),
                "--style_strength", str(style_strength),
                "--device", "cpu"
            ]
            
            # Set environment
            env = os.environ.copy()
            env['PYTHONPATH'] = os.pathsep.join([self.base_dir] + sys.path)
            
            logger.info(f"Running StyleTalk with command: {' '.join(cmd)}")
            
            # Run inference
            result = subprocess.run(
                cmd,
                cwd=os.path.abspath("."),  # Use project root directory
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not os.path.exists(output_path):
                raise RuntimeError("StyleTalk did not generate output")
            
            logger.info(f"StyleTalk generation completed: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"StyleTalk error: {e.stderr}")
            raise RuntimeError(f"StyleTalk inference failed: {e.stderr}")
        except Exception as e:
            logger.error(f"StyleTalk error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            'name': 'styletalk',
            'display_name': 'StyleTalk',
            'description': 'One-shot talking head with style control',
            'cpu_friendly': True,
            'quality_range': (64, 256),
            'fps_range': (10, 25),
            'default_quality': 128,
            'default_fps': 15,
            'has_style_control': True
        }


# Model registry
MODEL_REGISTRY: Dict[str, ModelBase] = {
    "wav2lip": Wav2LipWrapper(),
    "musetalk": MuseTalkWrapper(),
    "speech2lip": Speech2LipWrapper(),
    "styletalk": StyleTalkWrapper()
}


def get_available_models() -> Dict[str, Dict[str, Any]]:
    """Get information about available models."""
    available_models = {}
    for name, model in MODEL_REGISTRY.items():
        model_info = model.get_model_info()
        model_info['available'] = model.check_model_available()
        model_info['base_dir'] = model.base_dir
        available_models[name] = model_info
    return available_models


def generate_with_model(model_name: str, image_path: str, audio_path: str, output_path: str, **kwargs) -> str:
    """
    Generate lip-sync video using specified model.
    
    Args:
        model_name: Name of the model to use ('wav2lip' or 'musetalk')
        image_path: Path to input face image
        audio_path: Path to input audio file
        output_path: Path to save output video
        **kwargs: Additional model-specific parameters
    
    Returns:
        Path to generated video
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_name}. Available models: {list(MODEL_REGISTRY.keys())}")
    
    model = MODEL_REGISTRY[model_name]
    
    if not model.check_model_available():
        raise FileNotFoundError(f"Model {model_name} is not available. Please check model installation.")
    
    logger.info(f"Generating lip-sync video with {model_name}")
    return model.generate(image_path, audio_path, output_path, **kwargs)


def list_models() -> list:
    """List all available model names."""
    return list(MODEL_REGISTRY.keys())


def check_model_status(model_name: str) -> Dict[str, Any]:
    """Check the status of a specific model."""
    if model_name not in MODEL_REGISTRY:
        return {"error": f"Unknown model: {model_name}"}
    
    model = MODEL_REGISTRY[model_name]
    return model.get_model_info()
