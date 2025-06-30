import streamlit as st
import yt_dlp
import whisper
from gtts import gTTS
import os
import uuid
import tempfile
import traceback

# Configure Streamlit page
st.set_page_config(page_title="YouTube Dubber", layout="centered")
st.title("🎧 YouTube Subtitle & Dubbing App")

# Supported languages for gTTS
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
            st.warning("Please enter a YouTube video link.")
            return

        temp_dir = tempfile.mkdtemp()
        session_id = str(uuid.uuid4())
        temp_files = []

        try:
            # 1. Download Audio
            with st.spinner("⏳ Downloading audio from YouTube..."):
                audio_path = os.path.join(temp_dir, f"{session_id}.mp3")
                ydl_opts = {
                    'format': 'bestaudio[ext=webm]/bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, f"{session_id}.%(ext)s"),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])

                # Find actual mp3 file
                for file in os.listdir(temp_dir):
                    if file.endswith(".mp3"):
                        audio_path = os.path.join(temp_dir, file)
                        break

                if not os.path.exists(audio_path):
                    raise Exception("Audio download failed: MP3 file not found.")
                
                temp_files.append(audio_path)
                st.success("✅ Audio downloaded")

            # 2. Transcribe using Whisper
            with st.spinner("🧠 Transcribing audio (may take a few minutes)..."):
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                transcript = result["text"]
                st.success("✅ Transcription complete")

            # 3. Create SRT file
            with st.spinner("📝 Creating subtitle file..."):
                srt_path = os.path.join(temp_dir, f"{session_id}.srt")
                with open(srt_path, "w", encoding="utf-8") as f:
                    for i, segment in enumerate(result["segments"]):
                        start = format_timestamp(segment["start"])
                        end = format_timestamp(segment["end"])
                        f.write(f"{i+1}\n{start} --> {end}\n{segment['text'].strip()}\n\n")

                temp_files.append(srt_path)
                st.success("✅ Subtitle file created")

            # 4. Generate Dubbed Audio
            with st.spinner(f"🔊 Generating audio in {language_name}..."):
                dubbed_path = os.path.join(temp_dir, f"{session_id}_dub.mp3")
                tts = gTTS(text=transcript, lang=LANGUAGES[language_name])
                tts.save(dubbed_path)
                temp_files.append(dubbed_path)
                st.success("✅ Dubbed audio generated")

            # 5. Show results
            st.success("🎉 Done! Download or preview your results below.")
            col1, col2 = st.columns(2)
            with col1:
                with open(srt_path, "rb") as f:
                    st.download_button("📄 Download Subtitles (.srt)", f, file_name="subtitles.srt")

            with col2:
                with open(dubbed_path, "rb") as f:
                    st.download_button("🎧 Download Dubbed Audio (.mp3)", f, file_name="dubbed_audio.mp3")

            # Previews
            st.subheader("Transcript Preview")
            st.text_area("📝 Transcript", transcript, height=200)
            st.subheader("Dubbed Audio Preview")
            st.audio(dubbed_path)

        except Exception as e:
            st.error("❌ An error occurred")
            st.text(traceback.format_exc())

        finally:
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

def format_timestamp(seconds):
    millisec = int((seconds % 1) * 1000)
    seconds = int(seconds)
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hrs:02}:{mins:02}:{secs:02},{millisec:03}"

if __name__ == "__main__":
    main()
