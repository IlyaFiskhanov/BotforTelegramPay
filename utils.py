
import logging
from config import NUMBERS_FILE,USERS_FILE,DATABASE_FILE
from datetime import datetime, timedelta 
import json
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