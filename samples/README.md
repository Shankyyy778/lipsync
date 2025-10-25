# Sample Files

This directory contains sample input files for testing the lip-sync web app.

## Required Files

To test the application, you'll need:

1. **Sample Face Image** (`test_face.jpg` or `test_face.png`)
   - Clear, front-facing face image
   - Good lighting
   - High resolution (at least 256x256 pixels)
   - Supported formats: JPG, PNG

2. **Sample Audio File** (`test_audio.wav` or `test_audio.mp3`)
   - Clear speech audio
   - Duration: 5-30 seconds recommended
   - Supported formats: WAV, MP3
   - Sample rate: Any (will be converted to 16kHz)

## Getting Sample Files

### Face Images
- Use your own photos (with permission)
- Download from free stock photo sites
- Ensure the person in the image has given consent

### Audio Files
- Record your own voice
- Use free speech samples
- Ensure you have rights to use the audio

## Testing Workflow

1. Place sample files in this directory
2. Run the Streamlit app: `streamlit run app/streamlit_app.py`
3. Upload the sample files through the web interface
4. Select a model and generate the lip-sync video
5. Check the output in the `outputs/` directory

## Example File Names

```
samples/
├── test_face.jpg          # Sample face image
├── test_audio.wav         # Sample audio file
├── sample_speech.mp3      # Alternative audio format
└── README.md              # This file
```

## Notes

- Sample files are not included in the repository
- Add your own test files as needed
- Ensure all files have proper permissions and rights
