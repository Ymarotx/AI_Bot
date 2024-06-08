import asyncio
import io
import os
import aiohttp


from pathlib import Path

import aiofiles
import whisper
from aiogram.types import FSInputFile
from pydub import AudioSegment
import openai
from openai import AsyncOpenAI
from config_data.config import Config
import secrets

Config = Config()
client = AsyncOpenAI(api_key=Config.OpenAIToken)

async def client_files_create():
    file = await client.files.create(
        file=open('data.txt','rb'),
        purpose='assistants'
    )
    return file

async def client_assistants_create():
    file = await client_files_create()
    assistant = await client.beta.assistants.create(
        name='Example',
        description='You are example',
        instructions='Again example',
        model='gpt-3.5-turbo-1106',
        tools=[{"type": "code_interpreter"}],
        tool_resources={
            "code_interpreter": {
                "file_ids": [file.id]
            }
        }
    )
    return assistant.id

async def client_threads_create():
    file = await client_files_create()
    thread = await client.beta.threads.create(
        messages=[
            {
                'role': 'user',
                'content': 'Check db for example',
                'attachments': [
                    {
                    "file_id": file.id,
                    "tools": [{"type": "code_interpreter"}]
            }
          ]
        }
      ]
    )
    return thread.id


class AI_transformation_text:
    @classmethod
    async def get_text_from_voice(cls,voice_file):
        audio = AudioSegment.from_file(voice_file, format="ogg")
        generate_name = secrets.token_hex(2)
        mp3_file_path = f"{generate_name}.mp3"
        audio.export(mp3_file_path, format="mp3")
        with open(f'{mp3_file_path}','rb') as audio:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        return transcription.text,mp3_file_path


    @classmethod
    async def thread_run(cls,thread_id,assistant_id):
        run = await client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        return run.id

    @classmethod
    async def refresh_thread(cls,run_id,thread_id):
        refresh = await client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id,
        )
    @classmethod
    async def create_msg_from_user(cls,voice_file,thread_id):
        message,file_del = await cls.get_text_from_voice(voice_file)
        message_create = await client.beta.threads.messages.create(
            role='user',
            thread_id=thread_id,
            content=f'{message}'
        )
        return file_del
    @classmethod
    async def get_last_message(cls,thread_id):
        message = await client.beta.threads.messages.list(
            thread_id=thread_id
        )
        return message
    @classmethod
    async def assistant(cls,voice_file):
        thread_id = await client_threads_create()
        assistant_id = await client_assistants_create()
        file_del = await cls.create_msg_from_user(voice_file,thread_id)
        run_id = await cls.thread_run(thread_id=thread_id,assistant_id=assistant_id)
        await cls.refresh_thread(run_id,thread_id)
        messages = await cls.get_last_message(thread_id)
        try:
            return messages.data[0].content[0].text.value,file_del
        except IndexError:
            return "I don't understand" ,file_del

    @classmethod
    async def voice_answer(cls,voice_file):
        text_answer_for_voice,file_del = await cls.assistant(voice_file)
        generate_name = secrets.token_hex(2)
        speech_file_path = f"{generate_name}.mp3"
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=f"{text_answer_for_voice}"
        )
        response.stream_to_file(speech_file_path)
        voice_message = FSInputFile(f'{generate_name}.mp3')
        return voice_message,f'{generate_name}.mp3',file_del

