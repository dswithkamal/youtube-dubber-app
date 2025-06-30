import streamlit as st
import yt_dlp
import whisper
from gtts import gTTS
from pydub import AudioSegment
import os
import uuid

st.set_page_config(page_title="YouTube Dubber", layout="centered")

st.title("🎧 YouTube Subtitle & Dubbing App")

youtube_url = st.text_input("📺 Paste YouTube Video Link")

language = st.selectbox("🌐 Choose Language for Dubbing", ["hi", "en", "fr", "es", "de", "ta", "bn", "te", "ml", "ur"])

if st.button("🔁 Generate Subtitles & Dubbed Audio"):
    if not youtube_url:
        st.warning("Please paste a YouTube video link.")
        st.stop()

    with st.spinner("⏳ Downloading video..."):
        video_id = str(uuid.uuid4())
        audio_path = f"{video_id}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

    with st.spinner("🔍 Transcribing with Whisper..."):
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, fp16=False)
        transcript = result["text"]

        srt_path = f"{video_id}.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"]):
                f.write(f"{i+1}\n")
                f.write(f"{segment['start']:.2f} --> {segment['end']:.2f}\n")
                f.write(f"{segment['text']}\n\n")

    with st.spinner("🎙️ Generating dubbed audio..."):
        tts = gTTS(transcript, lang=language)
        dubbed_audio = f"{video_id}_dub.mp3"
        tts.save(dubbed_audio)

    st.success("✅ Done!")

    with open(srt_path, "rb") as f:
        st.download_button("📄 Download Subtitles (SRT)", f, file_name="subtitles.srt")

    with open(dubbed_audio, "rb") as f:
        st.download_button("🎧 Download Dubbed Audio (MP3)", f, file_name="dubbed_audio.mp3")

    os.remove(audio_path)
    os.remove(srt_path)
    os.remove(dubbed_audio)
