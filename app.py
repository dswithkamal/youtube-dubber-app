import streamlit as st
import yt_dlp
import whisper
from gtts import gTTS
import os
import uuid

# Mapping full language names to codes for gTTS
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Russian": "ru",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Tamil": "ta",
    "Bengali": "bn",
    "Malayalam": "ml",
    "Urdu": "ur"
}

st.set_page_config(page_title="YouTube Dubber", layout="centered")
st.title("🎧 YouTube Subtitle & Dubbing App")

youtube_url = st.text_input("📺 Paste YouTube Video Link")

language_name = st.selectbox("🌐 Choose Language for Dubbing", list(LANGUAGES.keys()))
language = LANGUAGES[language_name]

if st.button("🔁 Generate Subtitles & Dubbed Audio"):
    if not youtube_url:
        st.warning("⚠️ Please paste a YouTube video link.")
        st.stop()

    with st.spinner("⏳ Downloading audio from YouTube..."):
        video_id = str(uuid.uuid4())
        raw_path = f"{video_id}.webm"
        audio_path = f"{video_id}.mp3"

        ydl_opts = {
            'format': 'bestaudio[ext=webm]/bestaudio/best',
            'outtmpl': raw_path,
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            conversion = os.system(f"ffmpeg -y -i {raw_path} -vn -ar 44100 -ac 2 -b:a 192k {audio_path}")
            os.remove(raw_path)
            if conversion != 0:
                st.error("❌ Audio conversion to MP3 failed.")
                st.stop()
        except Exception as e:
            st.error("❌ Failed to download or convert audio.")
            st.exception(e)
            st.stop()

    with st.spinner("🧠 Transcribing using Whisper..."):
        try:
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, fp16=False)
        except Exception as e:
            st.error("❌ Whisper transcription failed.")
            st.exception(e)
            st.stop()

    transcript = result["text"]

    srt_path = f"{video_id}.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"]):
            f.write(f"{i+1}\n")
            f.write(f"{segment['start']:.2f} --> {segment['end']:.2f}\n")
            f.write(f"{segment['text']}\n\n")

    with st.spinner(f"🔊 Generating dubbed audio in {language_name}..."):
        try:
            tts = gTTS(transcript, lang=language)
            dubbed_audio = f"{video_id}_dub.mp3"
            tts.save(dubbed_audio)
        except Exception as e:
