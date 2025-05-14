import os
import io
from pathlib import Path
from fastapi import FastAPI, Request, Form, Response
from starlette.responses import PlainTextResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uuid
from generate_podcast import process_and_merge_podcasts
from multilingual import test_translations
from create_tavus_conversations import create_tavus_conversation
import requests
from pydub import AudioSegment
from groq import Groq
from fastapi import Body
import json




# Load environment variables
load_dotenv()

# Set up Groq client API key and base URL
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
print(f"GROQ_API_KEY: {os.getenv('GROQ_API_KEY')}")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in environment")

MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_API_URL = "https://tavusapi.com/v2/conversations"
PERSONA_ID = os.getenv("PERSONA_ID")
REPLICA_ID = os.getenv("REPLICA_ID")

# FastAPI app setup
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== MODELS ======
class PromptRequest(BaseModel):
    question: str

class TranslationRequest(BaseModel):
    text: str
    languages: list[str]

class ConversationRequest(BaseModel):
    person: str
    language: str
class Translations(BaseModel):
    language: str

# ====== ROUTES ======

@app.get("/")
def root():
    return {"message": "API is working"}

@app.post("/ask")
def ask_question(data: PromptRequest):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": data.question}]
            }
        )
        res_json = response.json()
        return {"response": res_json['choices'][0]['message']['content']}
    except Exception as e:
        return {"error": str(e)}

@app.post("/translate")
def translate(req: TranslationRequest):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    translations = {}
    for lang in req.languages:
        prompt = f"Translate the following English text to {lang}:\n{req.text}"
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            translations[lang] = content
        else:
            translations[lang] = f"Error: {response.status_code}"

    return {"translations": translations}


@app.post("/start-conversation")
def start_conversation(request: ConversationRequest):
    # Check for Tavus API key
    if not TAVUS_API_KEY:
        return JSONResponse(
            status_code=400,
            content={"error": "Tavus API key not configured. Please check your environment variables."}
        )

    try:
        with open("data/outputs/final.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)
        json_str = json.dumps(json_data, indent=2)
        
        payload = {
            "replica_id": REPLICA_ID,
            "persona_id": PERSONA_ID,
            "callback_url": "https://yourwebsite.com/webhook",
            "conversation_name": "A Conversation with " + request.person,
            'conversational_context': f"This is the metadata for all the videos:\n\n{json_str}",
            "custom_greeting": "Hey there " + request.person + ", long time no see!",
            "properties": {
                "max_call_duration": 3600,
                "participant_left_timeout": 60,
                "participant_absent_timeout": 300,
                "enable_recording": False,
                "enable_closed_captions": True,
                "apply_greenscreen": True,
                "language": request.language
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": TAVUS_API_KEY
        }

        response = requests.post(TAVUS_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            error_text = response.text
            if "replica has not been upgraded to enable streaming" in error_text:
                error_message = "This feature requires a Tavus streaming-enabled replica. Please contact support to upgrade or create a new replica with streaming enabled."
            else:
                error_message = f"Tavus API error: {error_text}"
            
            print(f"Error from Tavus API: Status {response.status_code}, Message: {error_text}")  # Debug log
            return JSONResponse(
                status_code=400,
                content={"error": error_message}
            )
            
    except FileNotFoundError:
        return JSONResponse(
            status_code=400,
            content={"error": "Video metadata file not found. Please ensure you've processed some videos first."}
        )
    except Exception as e:
        print(f"Unexpected error in start_conversation: {str(e)}")  # Debug log
        return JSONResponse(
            status_code=500,
            content={"error": f"Server error: {str(e)}"}
        )

@app.post("/generate-podcast")
def generate_podcast():
    try:
        result = process_and_merge_podcasts()
        return JSONResponse(content={"message": "Podcast created", "result": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/test-translations")
def run_translation(request: Translations = Body(...)):
    result = test_translations(request.language)
    return JSONResponse(content=result)

@app.post("/generate-audio")
def generate_audio(request: Request, filename: str = Form(...)):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TTS_MODEL = "playai-tts"
    VOICE = "Aaliyah-PlayAI"
    url = "https://api.groq.com/openai/v1/audio/speech"

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            podcast_text = file.read()

        if len(podcast_text) <= 9999:
            chunks = [podcast_text]
        else:
            # Split at sentence boundaries (or fallback to 9000-character chunks)
            import re
            sentences = re.split(r'(?<=[.!?])\s+', podcast_text)
            chunks, current = [], ""
            for sentence in sentences:
                if len(current) + len(sentence) < 9000:
                    current += sentence + " "
                else:
                    chunks.append(current.strip())
                    current = sentence + " "
            if current:
                chunks.append(current.strip())

        # Store each audio part
        audio_segments = []
        for i, chunk in enumerate(chunks):
            payload = {
                "model": TTS_MODEL,
                "input": chunk,
                "voice": VOICE,
                "response_format": "mp3"
            }

            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                return JSONResponse(status_code=response.status_code, content={"error": response.text})

            # Save temp MP3
            temp_file = f"chunk_{uuid.uuid4().hex}.mp3"
            with open(temp_file, "wb") as f:
                f.write(response.content)

            audio_segments.append(AudioSegment.from_mp3(temp_file))
            os.remove(temp_file)

        # Combine all segments
        final_audio = sum(audio_segments)
        output_path = f"combined_{uuid.uuid4().hex}.mp3"
        final_audio.export(output_path, format="mp3")

        return FileResponse(output_path, media_type="audio/mpeg", filename="full_podcast.mp3")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/generate-audio-groq")
def generate_audio_groq(filename: str = Form(...)):
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        # Read the text from the specified file
        with open(filename, 'r') as file:
            podcast_text = file.read()

        # Groq TTS parameters
        model = "playai-tts"
        voice = "Fritz-PlayAI"
        response_format = "wav"
        speech_file_path = f"speech_{os.path.basename(filename).split('.')[0]}.wav"

        # Generate the audio
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=podcast_text,
            response_format=response_format
        )

        response.write_to_file(speech_file_path)

        return FileResponse(speech_file_path, media_type="audio/wav", filename=speech_file_path)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
@app.post("/create_tavus_conversation")
def run_translation():
    result = create_tavus_conversation()
    return JSONResponse(content=result)

@app.post("/generate-speech")
def generate_speech():
    try:
        # Check for API key
        if not GROQ_API_KEY:
            return JSONResponse(
                status_code=500,
                content={"error": "GROQ_API_KEY not configured"}
            )

        # Read podcast text
        try:
            with open('podcasts/full_podcast.txt', 'r', encoding='utf-8') as file:
                podcast_text = file.read()
                if not podcast_text.strip():
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Podcast text is empty"}
                    )
        except FileNotFoundError:
            return JSONResponse(
                status_code=404,
                content={"error": "Podcast text file not found"}
            )

        # Split text into chunks of 9000 characters (leaving some buffer)
        # Try to split at sentence boundaries
        def split_into_chunks(text, max_length=9000):
            chunks = []
            current_chunk = ""
            sentences = text.split('. ')
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 <= max_length:  # +2 for '. '
                    current_chunk += sentence + '. '
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence + '. '
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            return chunks

        text_chunks = split_into_chunks(podcast_text)

        # Generate speech for each chunk
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Store audio chunks
            audio_chunks = []
            
            for chunk in text_chunks:
                response = requests.post(
                    "https://api.groq.com/openai/v1/audio/speech",
                    headers=headers,
                    json={
                        "model": "playai-tts",
                        "input": chunk,
                        "voice": "Fritz-PlayAI",
                        "response_format": "wav"
                    }
                )

                if not response.ok:
                    return JSONResponse(
                        status_code=response.status_code,
                        content={"error": f"Groq API error: {response.text}"}
                    )
                
                audio_chunks.append(io.BytesIO(response.content))

            # Combine audio chunks using pydub
            from pydub import AudioSegment
            
            combined = AudioSegment.empty()
            for chunk in audio_chunks:
                chunk.seek(0)
                segment = AudioSegment.from_wav(chunk)
                combined += segment

            # Convert combined audio to bytes
            output = io.BytesIO()
            combined.export(output, format="wav")
            output.seek(0)

            # Return the combined audio
            return Response(
                content=output.read(),
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=podcast.wav"}
            )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to generate speech: {str(e)}"}
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Unexpected error: {str(e)}"}
        )
    
@app.get("/podcast-text", response_class=PlainTextResponse)
async def get_podcast_text():
    file_path = Path("podcasts/full_podcast.txt")
    if not file_path.exists():
        return PlainTextResponse("File not found", status_code=404)
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()