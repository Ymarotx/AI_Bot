import io
import os

from aiogram import Router, Bot,F
from aiogram.filters import CommandStart
from aiogram.types import Message
import whisper
from pydub import AudioSegment
from aiogram.enums.content_type import ContentType

from services.services import AI_transformation_text
from lexicon.lexicon import LEXICON_MAIN
router: Router = Router()

@router.message(CommandStart())
async def command_start(message:Message):
    await message.answer(text=LEXICON_MAIN['start'])

@router.message(F.voice)
async def get_voice(message:Message,
                    bot:Bot):
    voice = message.voice
    file = await bot.get_file(voice.file_id)
    voice_file = await bot.download_file(file.file_path)
    res_voice,file_del_1,file_del_2 = await AI_transformation_text.voice_answer(voice_file=voice_file)
    await message.answer_voice(res_voice)
    os.remove(file_del_1)
    os.remove(file_del_2)

@router.message(~F.voice)
async def echo(message:Message):
    await message.answer(text=LEXICON_MAIN['echo'])