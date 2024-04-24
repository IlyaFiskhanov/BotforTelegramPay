
import logging
import json
from datetime import datetime, timedelta 
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types.message import ContentType
from aiogram.utils import executor
from aiogram import Bot, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.INFO)

TOKEN = "6432153368:AAFfS9eENYMSNDKYz2W85_g0mgLacS5v-lE"
PAYMENTS_TOKEN = "381764678:TEST:68354"
YOUR_TELEGRAM_USER_ID = "439047878"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Цена подписки (в копейках)
PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=1000 * 100)

# Файл с доступными номерами
NUMBERS_FILE = "numbers.txt"

# Файл для хранения имен пользователей с номерами
USERS_FILE = "usernames.txt"

# JSON-файл для базы данных
DATABASE_FILE = "database.json"

# Функция для поиска пользователя в базе данных
def find_user_in_database(username, database):
    for entry in database:
        if entry["username"] == username:
            return entry
    return None

# Функция для чтения и удаления первого номера из файла
def get_next_number():
    try:
        with open(NUMBERS_FILE, "r") as file:
            numbers = file.readlines()
            if numbers:
                next_number = numbers[0].strip()
                del numbers[0]  # Удаление использованного номера
                with open(NUMBERS_FILE, "w") as updated_file:
                    updated_file.writelines(numbers)
                return next_number
    except Exception as e:
        logging.error(f"Error reading number: {str(e)}")
    return None

# Функция для сохранения имени пользователя с номером в файле
def save_username_with_number(number, username):
    try:
        with open(USERS_FILE, "a") as file:
            file.write(f"Number: {number}, Username: {username}\n")
    except Exception as e:
        logging.error(f"Error saving username with number: {str(e)}")

# Функция для отправки сообщения в ваш аккаунт Telegram
async def send_notification_to_admin(message):
    try:
        await bot.send_message(YOUR_TELEGRAM_USER_ID, message)
    except Exception as e:
        logging.error(f"Error sending notification: {str(e)}")

# Функция для проверки прошло ли 30 дней с последнего платежа
def can_make_payment(username):
    try:
        with open(DATABASE_FILE, "r") as file:
            database = json.load(file)

        for entry in database:
            if entry["username"] == username:
                last_payment_date = datetime.strptime(entry["payment_date"], "%Y-%m-%d %H:%M:%S")
                current_date = datetime.now()
                if current_date - last_payment_date < timedelta(seconds=30):
                    return False
        return True 
    except Exception as e:
        logging.error(f"Error checking payment eligibility: {str(e)}")
    return False

# Функция для обновления JSON-базы данных с данными пользователя в виде столбцов
def update_json_database(data):
    try:
        with open(DATABASE_FILE, "r") as file:
            database = json.load(file)

        now = datetime.now()
        payment_date = now.strftime("%Y-%m-%d %H:%M:%S")

        # Вычисление следующей даты платежа (через 30 дней от текущей даты)
        next_payment_date = (now + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M:%S")

        # Создание новой записи с колонками
        new_entry = {
            "username": data["username"],
            "number": data["number"],
            "payment_amount": data["payment_amount"],
            "currency": data["currency"],
            "payment_date": payment_date,
            "next_payment_date": next_payment_date
        }

        database.append(new_entry)

        with open(DATABASE_FILE, "w") as file:
            json.dump(database, file, indent=4)  # Красивый вывод с отступами
    except Exception as e:
        logging.error(f"Error updating JSON database: {str(e)}")

# Функция для проверки активной подписки у пользователя
def has_active_subscription(username):
    try:
        with open(DATABASE_FILE, "r") as file:
            database = json.load(file)

        for entry in database:
            if entry["username"] == username:
                current_date = datetime.now()
                next_payment_date = datetime.strptime(entry["next_payment_date"], "%Y-%m-%d %H:%M:%S")
                if current_date < next_payment_date:
                    return True
        return False
    except Exception as e:
        logging.error(f"Error checking active subscription: {str(e)}")
    return False

# Функция для получения следующей даты платежа пользователя
def get_next_payment_date(username):
    try:
        with open(DATABASE_FILE, "r") as file:
            database = json.load(file)

        for entry in database:
            if entry["username"] == username:
                return entry["next_payment_date"]
    except Exception as e:
        logging.error(f"Error getting next payment date: {str(e)}")
    return None

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
