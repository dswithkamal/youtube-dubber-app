import streamlit as st
import yt_dlp
import whisper
from gtts import gTTS
import os
import uuid
import subprocess  # Better than os.system for ffmpeg

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

# Set page config
st.set_page_config(page_title="YouTube Dubber", layout="centered")
st.title("🎧 YouTube Subtitle & Dubbing App")

# Add session state to track processing status
if 'processing' not in st.session_state:
    st.session_state.processing = False

youtube_url = st.text_input("📺 Paste YouTube Video Link")

language_name = st.selectbox("🌐 Choose Language for Dubbing", list(LANGUAGES.keys()))
language = LANGUAGES[language_name]

def cleanup_files(*files):
    """Helper function to clean up temporary files"""
    for file in files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except Exception as e:
                st.warning(f"Couldn't delete temporary file {file}: {str(e)}")

if st.button("🔁 Generate Subtitles & Dubbed Audio") and not st.session_state.processing:
    if not youtube_url:
        st.warning("⚠️ Please paste a YouTube video link.")
        st.stop()

    st.session_state.processing = True
    
    try:
        video_id = str(uuid.uuid4())
        raw_path = f"{video_id}.webm"
        audio_path = f"{video_id}.mp3"
        srt_path = f"{video_id}.srt"
        dubbed_audio = f"{video_id}_dub.mp3"

        # Download audio from YouTube
        with st.spinner("⏳ Downloading audio from YouTube..."):
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': raw_path,
                'quiet': True,
                'extract_audio': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])
                # Rename the output file (yt-dlp adds extension based on format)
                downloaded_audio = raw_path.replace('.webm', '.mp3')
                if os.path.exists(downloaded_audio):
                    os.rename(downloaded_audio, audio_path)
            except Exception as e:
                st.error("❌ Failed to download audio.")
                st.exception(e)
                cleanup_files(raw_path, audio_path)
                st.session_state.processing = False
                st.stop()

        # Transcribe with Whisper
        with st.spinner("🧠 Transcribing using Whisper..."):
            try:
                model = whisper.load_model("base")
                result = model.transcribe(audio_path, fp16=False)
                transcript = result["text"]
                
                # Generate SRT file
                with open(srt_path, "w", encoding="utf-8") as f:
                    for i, segment in enumerate(result["segments"]):
                        f.write(f"{i+1}\n")
                        f.write(f"{segment['start']:.2f} --> {segment['end']:.2f}\n")
                        f.write(f"{segment['text']}\n\n")
            except Exception as e:
                st.error("❌ Whisper transcription failed.")
                st.exception(e)
                cleanup_files(raw_path, audio_path, srt_path)
                st.session_state.processing = False
                st.stop()

        # Generate dubbed audio
        with st.spinner(f"🔊 Generating dubbed audio in {language_name}..."):
            try:
                # Split text into chunks to avoid gTTS length limits
                max_chars = 5000  # gTTS has a character limit
                chunks = [transcript[i:i+max_chars] for i in range(0, len(transcript), max_chars)]
                
                # Generate audio for each chunk and combine
                temp_files = []
                for i, chunk in enumerate(chunks):
                    chunk_file = f"{video_id}_chunk_{i}.mp3"
                    tts = gTTS(chunk, lang=language)
                    tts.save(chunk_file)
                    temp_files.append(chunk_file)
                
                # Combine chunks if needed
                if len(temp_files) > 1:
                    with open("file_list.txt", "w") as f:
                        for file in temp_files:
                            f.write(f"file '{file}'\n")
                    
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                        "-i", "file_list.txt", "-c", "copy", dubbed_audio
                    ], check=True)
                    cleanup_files("file_list.txt", *temp_files)
                else:
                    os.rename(temp_files[0], dubbed_audio)
                    
            except Exception as e:
                st.error(f"❌ Text-to-speech failed for {language_name}.")
                st.exception(e)
                cleanup_files(raw_path, audio_path, srt_path, dubbed_audio, *temp_files)
                st.session_state.processing = False
                st.stop()

        st.success("✅ Done! Download your files below:")

        # Display and download results
        col1, col2 = st.columns(2)
        with col1:
            with open(srt_path, "rb") as f:
                st.download_button(
                    "📄 Download Subtitles (SRT)", 
                    f, 
                    file_name="subtitles.srt",
                    disabled=st.session_state.processing
                )
        with col2:
            with open(dubbed_audio, "rb") as f:
                st.download_button(
                    "🎧 Download Dubbed Audio (MP3)", 
                    f, 
                    file_name="dubbed_audio.mp3",
                    disabled=st.session_state.processing
                )

        # Preview sections
        st.subheader("Transcript Preview")
        st.text_area("Transcript", transcript, height=150)

        st.subheader("Audio Preview")
        st.audio(dubbed_audio)

    finally:
        # Clean up temporary files
        cleanup_files(raw_path, audio_path, srt_path, dubbed_audio)
        st.session_state.processing = False
