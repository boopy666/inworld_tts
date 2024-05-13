import gradio as gr
import simpleaudio as sa
import requests
import json
import base64
import io
import wave
import re
import html

params = {
    "display_name": "Inworld TTS",
    "is_tab": False
}

tts_params = {
    "api_key": "N3VXV0ZRMVFVQVhQMEt3emZDYjhHaTV4bjlQZ3hzQk46V0szOHZsdUZ6TjFrZ2pRWTB3NndsVTlLMWxJN2ExZEJqSVJVOFJsbG4xdGZXdE9VeUg3MjViT0lYYjVZajZJWQ=="
}


def output_modifier(string, state, is_chat=True):
    api_key = tts_params.get('api_key', '')

    if api_key:
        try:
            print("Fetching voices...")
            voices = fetch_voices(api_key)
            if voices:
                print("Voices fetched successfully.")
                print("Synthesizing speech...")
                synthesize_speech_chunks(api_key, string)
                print("Speech synthesized and played successfully.")
            else:
                print("No voices found.")
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        print("API key not provided.")

    return string


def fetch_voices(api_key):
    url = 'https://api.inworld.ai/tts/v1alpha/voices'
    headers = {
        'Authorization': 'Basic ' + api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching voices: {str(e)}")


def synthesize_speech_chunks(api_key, text):
    #sanatize the text
    text = sanitize_text(text)
    # Split the text into chunks of approximately 500 characters
    chunks = split_text_into_chunks(text, 200)

    for chunk in chunks:
        synthesize_speech(api_key, chunk)


def split_text_into_chunks(text, chunk_size):
    # Split the text into sentences based on "!", "?", or "."
    sentences = re.split(r'(?<=[!?.])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def sanitize_text(text):
    # Remove text between asterisks or square brackets
    text = re.sub(r'\*[^*]*\*', '', text)
    text = re.sub(r'\[[^]]*\]', '', text)

    # Remove emoticons
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)

    # Unescape the input text
    print(f"\n\n\nDebug pre unescape: {text}\n\n\n")
    # Replace specific escaped characters with their original form
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;', "'", text)
    text = re.sub(r'&#x27;', "'", text)
    text = re.sub(r'&#33;', '!', text)
    text = re.sub(r'&#63;', '?', text)
    text = re.sub(r'&#44;', ',', text)
    text = re.sub(r'&#46;', '.', text)
    text = re.sub(r'&#58;', ':', text)
    text = re.sub(r'&#59;', ';', text)
    text = re.sub(r'&#40;', '(', text)
    text = re.sub(r'&#41;', ')', text)
    text = re.sub(r'&#91;', '[', text)
    text = re.sub(r'&#93;', ']', text)
    text = re.sub(r'&#123;', '{', text)
    text = re.sub(r'&#125;', '}', text)
    print(f"\n\n\nDebug POST unescape: {text}\n\n\n")

    return text


def synthesize_speech(api_key, text):

    print(f"\n\n\nCurrent chunk: {text}\n\n\n")

    url = 'https://api.inworld.ai/tts/v1alpha/text:synthesize'
    headers = {
        'Authorization': 'Basic ' + api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'input': {
            'text': json.dumps(str(text))
        },
        'voice': {
            'name': 'Rachel'
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {str(e)}")
            print(f"Response content: {response.text}")
            raise Exception("Error decoding JSON response")

        audio_content = response_data['result']['audioContent']

        # Decode the base64-encoded audio content
        audio_data = base64.b64decode(audio_content)

        # Create a WAV file in memory from the audio data
        wav_file = io.BytesIO()
        with wave.open(wav_file, 'wb') as wave_writer:
            wave_writer.setnchannels(1)  # Mono audio
            wave_writer.setsampwidth(2)  # 16-bit audio
            wave_writer.setframerate(24000)  # Sampling rate of 24000Hz
            wave_writer.writeframes(audio_data)

        # Rewind the WAV file
        wav_file.seek(0)

        # Load the WAV file using simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(wav_file)

        # Play the audio
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error synthesizing speech: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing audio: {str(e)}")


def ui():
    with gr.Blocks() as demo:
        with gr.Accordion(label="Inworld TTS", open=True):
            api_key = gr.Textbox(
                label="Inworld API Key",
                value=tts_params["api_key"],
                placeholder="Enter your API key here..."
            )
            submit_button = gr.Button("Commit API Key")

        def commit_api_key(api_key_value):
            tts_params["api_key"] = api_key_value
            print("API key committed successfully.")

        submit_button.click(
            fn=commit_api_key,
            inputs=[api_key],
            outputs=[]
        )

    return demo


if __name__ == "__main__":
    ui = ui()
    ui.launch()