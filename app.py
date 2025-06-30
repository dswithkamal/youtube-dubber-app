import streamlit as st
import yt_dlp
import whisper
import os
import uuid
import tempfile
import traceback
import ffmpeg

# Page config
st.set_page_config(page_title="YouTube Subtitle Generator", layout="centered")
st.title("📝 YouTube Subtitle Generator")

# Whisper supported translation targets
LANGUAGES = {
    "Original Audio Language": None,
    "Translate to English": "en",
    "Translate to Hindi": "hi",
    "Translate to Spanish": "es",
    "Translate to Russian": "ru",
    "Translate to French": "fr",
    "Translate to German": "de",
    "Translate to Japanese": "ja"
}

def format_timestamp(seconds):
    millisec = int((seconds % 1) * 1000)
    seconds = int(seconds)
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hrs:02}:{mins:02}:{secs:02},{millisec:03}"

def main():
    youtube_url = st.text_input("📺 Paste YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    translation_lang = st.selectbox("🌐 Subtitle Language", list(LANGUAGES.keys()))

    if st.button("Generate Subtitles (.srt)"):
        if not youtube_url:
            st.warning("⚠️ Please enter a YouTube video link.")
            return

        temp_dir = tempfile.mkdtemp()
        session_id = str(uuid.uuid4())
        temp_files = []

        try:
            with st.spinner("⏳ Downloading and converting audio..."):
                raw_audio = os.path.join(temp_dir, f"{session_id}.webm")
                mp3_audio = os.path.join(temp_dir, f"{session_id}.mp3")

                # Download using yt-dlp
                ydl_opts = {
                    'format': 'bestaudio[ext=webm]/bestaudio/best',
                    'outtmpl': raw_audio,
                    'quiet': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])

                if not os.path.exists(raw_audio):
                    raise Exception("Audio download failed")

                # Convert using ffmpeg-python
                ffmpeg.input(raw_audio).output(mp3_audio, format='mp3', acodec='libmp3lame').run(overwrite_output=True, quiet=True)
                temp_files.extend([raw_audio, mp3_audio])

            # Transcribe or translate
            with st.spinner("🧠 Transcribing audio with Whisper..."):
                model = whisper.load_model("base")
                result = model.transcribe(mp3_audio, task="translate" if LANGUAGES[translation_lang] else "transcribe", language=LANGUAGES[translation_lang] or None)
                transcript = result["text"]

            # Generate SRT
            with st.spinner("📄 Generating SRT file..."):
                srt_path = os.path.join(temp_dir, f"{session_id}.srt")
                with open(srt_path, "w", encoding="utf-8") as f:
                    for i, seg in enumerate(result["segments"]):
                        start = format_timestamp(seg["start"])
                        end = format_timestamp(seg["end"])
                        f.write(f"{i+1}\n{start} --> {end}\n{seg['text'].strip()}\n\n")
                temp_files.append(srt_path)

            st.success("✅ Subtitles ready!")

            with open(srt_path, "rb") as f:
                st.download_button("📥 Download Subtitles (.srt)", f, file_name="subtitles.srt")

            st.subheader("Transcript Preview")
            st.text_area("📝 Transcript", transcript, height=250)

        except Exception as e:
            st.error("❌ An error occurred:")
            st.text(traceback.format_exc())
        finally:
            for file in temp_files:
                try: os.remove(file)
                except: pass
            try: os.rmdir(temp_dir)
            except: pass

if __name__ == "__main__":
    main()
