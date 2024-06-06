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
from openai import OpenAI
from config_data.config import Config
import secrets

client = OpenAI(api_key=Config.OpenAIToken)

file = client.files.create(
    file=open('data.txt','rb'),
    purpose='assistants'
)

assistant = client.beta.assistants.create(
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

thread = client.beta.threads.create(
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
assistant_id = assistant.id
thread_id = thread.id


class AI_transformation_text:
    @classmethod
    async def get_text_from_voice(cls,voice_file):
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {Config.OpenAIToken}",
        }
        audio = AudioSegment.from_file(voice_file, format="ogg")
        generate_name = secrets.token_hex(2)
        mp3_file_path = f"{generate_name}.mp3"
        audio.export(mp3_file_path, format="mp3")
        with open(mp3_file_path,'rb') as file:
            mp3 = file.read()
        data = aiohttp.FormData()
        data.add_field('file',mp3,filename=mp3_file_path)
        data.add_field('model','whisper-1')
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result,mp3_file_path
                else:
                    return None,f"{mp3_file_path}"

    @classmethod
    async def thread_run(cls):
        url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
        headers = {
            "Authorization": f"Bearer {Config.OpenAIToken}",
            "Content-Type" : "application/json",
            "OpenAI-Beta" : "assistants=v2",
        }
        data = {
                "assistant_id": f"{assistant_id}",
                "model": "gpt-4o",
                "instructions": "New instructions that override the Assistant instructions",
                "tools": [{"type": "code_interpreter"}, {"type": "file_search"}]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['id']
                else:
                    return None
    @classmethod
    async def refresh_thread(cls,run_id):
        refresh = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id,
        )
    @classmethod
    async def create_msg_from_user(cls,voice_file):
        message,file_del = await cls.get_text_from_voice(voice_file)
        message_create = client.beta.threads.messages.create(
            role='user',
            thread_id=thread_id,
            content=f'{message}'
        )
        return file_del
    @classmethod
    async def get_last_message(cls):
        message = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        return message
    @classmethod
    async def assistant(cls,voice_file):
        file_del = await cls.create_msg_from_user(voice_file)
        run_id = await cls.thread_run()
        await cls.refresh_thread(run_id)
        messages = await cls.get_last_message()
        try:
            return messages.data[0].content[0].text.value,file_del
        except IndexError:
            return "I don't understand" ,file_del

    @classmethod
    async def request_audio_speech_create(cls,text_answer_for_voice):
        response_task = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=f"{text_answer_for_voice}"
        )
        return response_task

    @classmethod
    async def voice_answer(cls,voice_file):
        text_answer_for_voice,file_del = await cls.assistant(voice_file)
        generate_name = secrets.token_hex(2)
        speech_file_path = Path(__file__).parent / f"{generate_name}.mp3"
        # response_task = asyncio.create_task(cls.request_audio_speech_create(text_answer_for_voice))
        # response = await response_task
        url = f"https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {Config.OpenAIToken}",
            "Content-Type" : "application/json",
        }
        data = {
            "model": "tts-1",
            "input": f"{text_answer_for_voice}",
            "voice": "alloy"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    audio = await response.read()
                    with open(f'{generate_name}.mp3','wb') as file:
                        file.write(audio)
                else:
                    return None
        voice_message = FSInputFile(f'{generate_name}.mp3')
        return voice_message,f'{generate_name}.mp3',file_del

