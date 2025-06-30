import streamlit as st
import yt_dlp
import whisper
from gtts import gTTS
import os
import uuid
import tempfile
import subprocess

# Configure app
st.set_page_config(page_title="YouTube Dubber", layout="centered")
st.title("🎧 YouTube Subtitle & Dubbing App")

# Language mapping
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Russian": "ru",
    "Chinese": "zh",
    "Arabic": "ar",
    "Portuguese": "pt",
    "Telugu": "te",
    "Tamil": "ta",
    "Bengali": "bn"
}

def clean_temp_files(files):
    """Safely remove temporary files"""
    for file in files:
        try:
            if file and os.path.exists(file):
                os.remove(file)
        except:
            pass

def main():
    youtube_url = st.text_input("📺 Paste YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    language_name = st.selectbox("🌐 Select Dubbing Language", list(LANGUAGES.keys()))
    
    if st.button("🔁 Generate Subtitles & Dubbed Audio"):
        if not youtube_url:
            st.warning("Please enter a YouTube URL")
            return
            
        # Create temporary workspace
        temp_dir = tempfile.mkdtemp()
        temp_files = []
        
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # 1. Download audio
            with st.spinner("⏳ Downloading video audio..."):
                try:
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(temp_dir, f'{session_id}.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                        }],
                        'quiet': True
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(youtube_url, download=True)
                        original_audio = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                        temp_files.append(original_audio)
                except Exception as e:
                    st.error(f"❌ Download error: {str(e)}")
                    return
            
            # 2. Transcribe with Whisper
            with st.spinner("🧠 Transcribing audio..."):
                try:
                    model = whisper.load_model("base")
                    result = model.transcribe(original_audio)
                    transcript = result["text"]
                except Exception as e:
                    st.error(f"❌ Transcription failed: {str(e)}")
                    return
            
            # 3. Generate SRT subtitles
            with st.spinner("📝 Creating subtitles..."):
                try:
                    srt_file = os.path.join(temp_dir, f'{session_id}_subtitles.srt')
                    with open(srt_file, 'w', encoding='utf-8') as f:
                        for i, segment in enumerate(result["segments"]):
                            f.write(f"{i+1}\n")
                            f.write(f"{segment['start']:.3f} --> {segment['end']:.3f}\n")
                            f.write(f"{segment['text'].strip()}\n\n")
                    temp_files.append(srt_file)
                except Exception as e:
                    st.error(f"❌ Subtitle creation failed: {str(e)}")
                    return
            
            # 4. Generate dubbed audio
            with st.spinner(f"🔊 Creating {language_name} dubbed audio..."):
                try:
                    # Use system ffmpeg for audio concatenation
                    dubbed_audio = os.path.join(temp_dir, f'{session_id}_dubbed.mp3')
                    
                    # Directly generate audio without splitting
                    tts = gTTS(transcript, lang=LANGUAGES[language_name])
                    tts.save(dubbed_audio)
                    temp_files.append(dubbed_audio)
                except Exception as e:
                    st.error(f"❌ Dubbing failed: {str(e)}")
                    return
            
            # 5. Display results
            st.success("✅ Processing complete!")
            
            # Create download buttons
            col1, col2 = st.columns(2)
            with col1:
                with open(srt_file, 'rb') as f:
                    st.download_button(
                        "📄 Download Subtitles (SRT)",
                        f,
                        file_name="subtitles.srt"
                    )
            
            with col2:
                with open(dubbed_audio, 'rb') as f:
                    st.download_button(
                        "🎧 Download Dubbed Audio",
                        f,
                        file_name="dubbed_audio.mp3"
                    )
            
            # Add previews
            st.subheader("Preview")
            st.audio(dubbed_audio)
            st.text_area("Generated Transcript", transcript, height=200)
            
        finally:
            # Clean up temporary files
            clean_temp_files(temp_files)
            try:
                os.rmdir(temp_dir)
            except:
                pass

if __name__ == "__main__":
    main()
