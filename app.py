import streamlit as st
import yt_dlp
import whisper
from gtts import gTTS
import os
import uuid
import tempfile
import subprocess
import traceback

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

def main():
    youtube_url = st.text_input("📺 Paste YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    language_name = st.selectbox("🌐 Select Dubbing Language", list(LANGUAGES.keys()))
    
    if st.button("🔁 Generate Subtitles & Dubbed Audio"):
        if not youtube_url:
            st.warning("Please enter a YouTube URL")
            return
            
        # Create temporary workspace
        temp_dir = tempfile.mkdtemp()
        session_id = str(uuid.uuid4())
        temp_files = []
        
        try:
            # 1. Download audio
            with st.spinner("⏳ Downloading video audio..."):
                try:
                    original_audio = os.path.join(temp_dir, f'{session_id}.mp3')
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(temp_dir, session_id),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                        }],
                        'quiet': True
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([youtube_url])
                    
                    # Find the actual audio file
                    for file in os.listdir(temp_dir):
                        if file.startswith(session_id) and file.endswith('.mp3'):
                            original_audio = os.path.join(temp_dir, file)
                            break
                    
                    if not os.path.exists(original_audio):
                        raise Exception("Audio download failed - no MP3 file found")
                        
                    temp_files.append(original_audio)
                    st.success("✅ Audio downloaded")
                except Exception as e:
                    st.error(f"❌ Download error: {str(e)}")
                    st.text(traceback.format_exc())
                    return
            
            # 2. Transcribe with Whisper
            with st.spinner("🧠 Transcribing audio (this may take a few minutes)..."):
                try:
                    model = whisper.load_model("base")
                    result = model.transcribe(original_audio)
                    transcript = result["text"]
                    st.success("✅ Transcription complete")
                except Exception as e:
                    st.error(f"❌ Transcription failed: {str(e)}")
                    st.text(traceback.format_exc())
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
                    st.success("✅ Subtitles created")
                except Exception as e:
                    st.error(f"❌ Subtitle creation failed: {str(e)}")
                    st.text(traceback.format_exc())
                    return
            
            # 4. Generate dubbed audio
            with st.spinner(f"🔊 Creating {language_name} dubbed audio..."):
                try:
                    dubbed_audio = os.path.join(temp_dir, f'{session_id}_dubbed.mp3')
                    tts = gTTS(transcript, lang=LANGUAGES[language_name])
                    tts.save(dubbed_audio)
                    temp_files.append(dubbed_audio)
                    st.success("✅ Dubbed audio created")
                except Exception as e:
                    st.error(f"❌ Dubbing failed: {str(e)}")
                    st.text(traceback.format_exc())
                    return
            
            # 5. Display results
            st.success("✅ Processing complete! Download your files below")
            
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
            
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            st.text(traceback.format_exc())
        finally:
            # Clean up temporary files
            for file in temp_files:
                try:
                    if os.path.exists(file):
                        os.remove(file)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass

if __name__ == "__main__":
    main()
