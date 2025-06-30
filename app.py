import streamlit as st
import yt_dlp
import whisper
from gtts import gTTS
import os
import uuid
import subprocess
from pydub import AudioSegment

# Configure app
st.set_page_config(page_title="YouTube Dubber Pro", layout="centered")
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
    "Portuguese": "pt"
}

def clean_temp_files(*files):
    """Safely remove temporary files"""
    for file in files:
        try:
            if file and os.path.exists(file):
                os.remove(file)
        except Exception as e:
            st.warning(f"Couldn't remove {file}: {str(e)}")

def main():
    youtube_url = st.text_input("📺 Paste YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    language_name = st.selectbox("🌐 Select Dubbing Language", list(LANGUAGES.keys()))
    
    if st.button("🔁 Generate Subtitles & Dubbed Audio"):
        if not youtube_url:
            st.warning("Please enter a YouTube URL")
            return

        with st.spinner("⏳ Processing your video..."):
            try:
                # Generate unique IDs for files
                session_id = str(uuid.uuid4())
                temp_files = []
                
                # 1. Download audio
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f'{session_id}_original',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }],
                    'quiet': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])
                original_audio = f'{session_id}_original.mp3'
                temp_files.append(original_audio)
                
                # 2. Transcribe with Whisper
                model = whisper.load_model("base")
                result = model.transcribe(original_audio)
                transcript = result["text"]
                
                # 3. Generate SRT
                srt_file = f'{session_id}_subtitles.srt'
                with open(srt_file, 'w', encoding='utf-8') as f:
                    for i, segment in enumerate(result["segments"]):
                        f.write(f"{i+1}\n")
                        f.write(f"{segment['start']:.3f} --> {segment['end']:.3f}\n")
                        f.write(f"{segment['text'].strip()}\n\n")
                temp_files.append(srt_file)
                
                # 4. Generate dubbed audio
                tts = gTTS(transcript, lang=LANGUAGES[language_name])
                dubbed_audio = f'{session_id}_dubbed.mp3'
                tts.save(dubbed_audio)
                temp_files.append(dubbed_audio)
                
                # 5. Display results
                st.success("✅ Processing complete!")
                
                col1, col2 = st.columns(2)
                with col1:
                    with open(srt_file, 'rb') as f:
                        st.download_button(
                            "📄 Download Subtitles",
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
                
                st.audio(dubbed_audio)
                st.text_area("Generated Transcript", transcript, height=200)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                clean_temp_files(*temp_files)

if __name__ == "__main__":
    main()
