import streamlit as st
import yt_dlp
import whisper
from gtts import gTTS
import os
import uuid

# Mapping full language names to language codes for gTTS
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
        st.warning("Please paste a YouTube video link.")
        st.stop()

    with st.spinner("⏳ Downloading audio from YouTube..."):
        video_id = str(uuid.uuid4())
        audio_path = f"{video_id}.m4a"
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': audio_path,
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
        except Exception as e:
            st.error("❌ Failed to download audio. Please check the video URL.")
            st.stop()

    with st.spinner("🧠 Transcribing audio using Whisper..."):
        model = whisper.load_model("base")
        try:
            result = model.transcribe(audio_path, fp16=False)
        except Exception as e:
            st.error("❌ Whisper transcription failed. Try a different video.")
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
            st.error(f"❌ Text-to-speech failed for {language_name}.")
            st.stop()

    st.success("✅ Done!")

    with open(srt_path, "rb") as f:
        st.download_button("📄 Download Subtitles (SRT)", f, file_name="subtitles.srt")

    with open(dubbed_audio, "rb") as f:
        st.download_button("🎧 Download Dubbed Audio (MP3)", f, file_name="dubbed_audio.mp3")

    # Cleanup temporary files
    os.remove(audio_path)
    os.remove(srt_path)
    os.remove(dubbed_audio)
