import io
from pathlib import Path

import whisper
from aiogram.types import FSInputFile
from pydub import AudioSegment
import openai
from openai import OpenAI
from config_data.config import Config
import secrets

client = OpenAI(api_key=Config.OpenAIToken)

class AI_transformation_text:
    @classmethod
    async def get_text_from_voice(cls,voice_file):
        audio = AudioSegment.from_file(voice_file, format="ogg")
        generate_name = secrets.token_hex(2)
        mp3_file_path = f"{generate_name}.mp3"
        audio.export(mp3_file_path, format="mp3")
        audio_file = open(f"{mp3_file_path}", "rb")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        return transcription

    @classmethod
    async def get_answer_for_question(cls,voice_file):
        openai.api_key = Config.OpenAIToken
        text = await cls.get_text_from_voice(voice_file)
        completion = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": f"{text}",
                },
            ],
        )
        return completion.choices[0].message.content

    @classmethod
    async def voice_answer(cls,voice_file):
        text_answer_for_voice = await cls.get_answer_for_question(voice_file)
        generate_name = secrets.token_hex(2)
        speech_file_path = Path(__file__).parent / f"{generate_name}.mp3"
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=f"{text_answer_for_voice}"
        )
        response.stream_to_file(speech_file_path)
        voice_message = FSInputFile(f'{speech_file_path}')
        return voice_message

