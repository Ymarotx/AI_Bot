import asyncio
import logging

from aiogram import Bot, Dispatcher
from config_data.config import Config
from handlers.user_handlers import router as user_hand_rout

logger = logging.getLogger(__name__)
Config = Config()
async def main():
    logging.basicConfig(level=logging.INFO,
                        # filename='logs.log',
                        format='%(filename)s:%(lineno)d #%(levelname)-8s'
                               '[%(asctime)s] - %(name)s - %(message)s'
                        )

    bot: Bot = Bot(token=Config.APIToken,parse_mode='HTML')
    dp: Dispatcher = Dispatcher()
    dp.include_router(user_hand_rout)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
