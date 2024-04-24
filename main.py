import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ParseMode
from config import TOKEN,PAYMENTS_TOKEN,YOUR_TELEGRAM_USER_ID,NUMBERS_FILE,USERS_FILE,DATABASE_FILE
from utils import find_user_in_database,get_next_number,save_username_with_number,can_make_payment,update_json_database,has_active_subscription,get_next_payment_date
from datetime import datetime, timedelta 
from aiogram import types
from aiogram.types.message import ContentType
from aiogram.utils import executor
from aiogram import Bot, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ParseMode
import json
# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=1000 * 100) # Цена подписки (в копейках)

# Функция для отправки сообщения в ваш аккаунт Telegram
async def send_notification_to_admin(message):
    try:
        await bot.send_message(YOUR_TELEGRAM_USER_ID, message)
    except Exception as e:
        logging.error(f"Error sending notification: {str(e)}")

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    # Приветственное сообщение
    welcome_message ="Добро пожаловать!\nХомячья Банда😏 - это уютное место, где вы можете получить доступ к эксклюзивным инвестиционным советам и присоединиться к сообществу единомышленников.\nНаш бот предоставляет возможность приобрести подписку на платный канал и получить доступ к актуальной информации и советам от Алексея.\nБот автоматически отслеживает оплаты, ведет базу данных активных подписчиков и предоставляет им уникальные номера для доступа."
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    subscribe_button = KeyboardButton("Оплатить подписку")
    markup.add(subscribe_button)

    # Отправьте приветственное сообщение с клавиатурой
    await msg.answer(welcome_message, reply_markup=markup)
    await bot.send_sticker(msg.from_user.id, "CAACAgIAAxkBAAEKfwNlJSdEb1l8KF8paILuf79oSoGuiQACSw0AAuw46ErDY7mJkZCxJTAE")

    # Сообщение описывающее команду /buy
    help_message = "Чтобы оплатить подписку\nнажмите /buy или отправьте сообщение\n'Оплатить подписку'"
    await msg.answer(help_message)

# Обработчик команды /buy и текстового сообщения 'Оплатить подписку'
@dp.message_handler(commands=['buy'], content_types=types.ContentType.TEXT)
@dp.message_handler(lambda message: message.text.lower() == 'оплатить подписку')
async def buy(msg: types.Message):
    username = msg.from_user.username

    if has_active_subscription(username):
        await bot.send_message(msg.from_user.id, "У вас уже активна подписка.")
    else:
        if not can_make_payment(username):
            await bot.send_message(msg.from_user.id, "Вы не можете оплатить подписку, так как не прошло 30 дней с последней оплаты.")
        else:
            await bot.send_invoice(msg.from_user.id,
                                   title="Подписка на платный канал",
                                   description="Активация подписка на канал 1 месяц",
                                   provider_token=PAYMENTS_TOKEN,
                                   currency="rub",
                                   photo_url = "https://i.ibb.co/g4h3NY2/image.png",
                                   photo_height=512,
                                   photo_width=512,
                                   photo_size=512,
                                   is_flexible=False,
                                   prices=[PRICE],
                                   start_parameter="one-month-subscription",
                                   payload="test-invoice-payload")
# Обработчик PreCheckoutQuery
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# Обработчик успешного платежа
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(msg: types.Message):
    payment_info = msg.successful_payment.to_python()
    total_amount = payment_info.get("total_amount", 0)
    currency = payment_info.get("currency", "")

    next_number = get_next_number()
    username = msg.from_user.username

    if next_number:
        save_username_with_number(next_number, username)

        # Загрузка существующей базы данных
        with open(DATABASE_FILE, "r") as file:
            database = json.load(file)

        # Поиск пользователя в базе данных
        user_entry = find_user_in_database(username, database)

        if user_entry:
            # Обновление данных существующего пользователя
            user_entry.update({
                "number": next_number,
                "payment_amount": total_amount,
                "currency": currency
            })
        else:
            # Создание новой записи пользователя
            user_entry = {
                "username": username,
                "number": next_number,
                "payment_amount": total_amount,
                "currency": currency,
                "payment_date": "",
                "next_payment_date": ""
            }

        # Обновление даты последнего платежа и следующей даты платежа пользователя
        now = datetime.now()
        payment_date = now.strftime("%Y-%m-%d %H:%M:%S")
        user_entry["payment_date"] = payment_date

        next_payment_date = (now + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M:%S")
        user_entry["next_payment_date"] = next_payment_date

        if not find_user_in_database(username, database):
            database.append(user_entry)

        with open(DATABASE_FILE, "w") as file:
            json.dump(database, file, indent=4)

        message_text = (
            f"Платёж на сумму {total_amount // 100} {currency} прошел успешно!!!\n"
            f"Ваш номер: <code>{next_number}</code>\n"
            f"Следующая оплата: {next_payment_date}" 

        )

        await bot.send_message(
            msg.from_user.id,
            message_text,
            parse_mode=ParseMode.HTML
        )

        await send_notification_to_admin(f"Пользователь {username} оплатил подписку. Номер: {next_number}")
    else:
        await bot.send_message(msg.from_user.id, "К сожалению, номеры закончились. Попробуйте позже.")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)

