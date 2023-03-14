import uvicorn
from fastapi.routing import APIRouter
from api.handlers import task_router
from fastapi import FastAPI
from aiogram import types, Dispatcher, Bot
from telegram.telegram_test import dp, bot, API_TOKEN,executor




app = FastAPI(title="Task manager")
main_api_router = APIRouter()


main_api_router.include_router(task_router, prefix="/task", tags=["task"])
app.include_router(main_api_router)

WEBHOOK_PATH = f"/bot/{API_TOKEN}"
WEBHOOK_URL = "http://localhost:8082" + WEBHOOK_PATH


@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL
        )


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

