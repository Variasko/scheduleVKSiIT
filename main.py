import os
import requests
import fitz  # PyMuPDF
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Ваш токен API
TOKEN = '7374673313:AAGV629dX6UUr7ixBliYHRMSNB9Nvl8GB7w'
ADMINS_ID = [797483196]
# URL PDF файлов
PDF_URLS = {
    "Получить расписание 1 корпус": 'https://rasp.vksit.ru/spo.pdf',
    "Получить расписание 2 корпус": 'https://rasp.vksit.ru/npo.pdf'
}

keyboard = [
    [KeyboardButton("Получить расписание 1 корпус")],
    [KeyboardButton("Получить расписание 2 корпус")],
    [KeyboardButton("Разработчик")],
    [KeyboardButton("Подписаться на рассылку")]
]

# Файл для хранения списка пользователей
USERS_FILE = 'users.txt'
USERS_FILE1 = 'users1.txt'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    user_id = update.message.from_user.id
    if is_user_subscribed1(user_id):
        pass
    else:
        with open(USERS_FILE1, 'a') as f:
            f.write(f'{user_id}\n')
    await update.message.reply_text('Привет! Что вы хотите сделать?', reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text

    if text in PDF_URLS:
        await send_schedule(update, context, PDF_URLS[text])
    elif text == "Разработчик":
        await creator(update, context)
    elif text == "Подписаться на рассылку":
        await subscribe(update, context)
    else:
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('Что вы хотите сделать?', reply_markup=reply_markup)

async def send_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE, pdf_url: str) -> None:
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()

        with open('schedule.pdf', 'wb') as f:
            f.write(response.content)

        # Конвертировать PDF в PNG с увеличенным разрешением
        doc = fitz.open('schedule.pdf')
        page = doc.load_page(0)  # Загрузить первую страницу
        zoom = 2  # Увеличить масштаб в 2 раза
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        image_path = 'schedule.png'
        pix.save(image_path)

        await update.message.reply_photo(photo=open(image_path, 'rb'))
    except requests.RequestException as e:
        await update.message.reply_text(f'Не удалось загрузить расписание. Ошибка: {e}')
    except Exception as e:
        await update.message.reply_text(f'Произошла ошибка при обработке PDF. Ошибка: {e}')

async def creator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Бота разработал студент группы ИСП-421п, Комиссаров Александр.'
                                    '\nПо всем вопросам обращаться к @tochnoNeSasha')

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_subscribed(user_id):
        await update.message.reply_text('Вы уже подписаны на рассылку!\nРасписание придёт в 3 часа')
    else:
        with open(USERS_FILE, 'a') as f:
            f.write(f'{user_id}\n')
        await update.message.reply_text('Вы подписались на рассылку!\nРасписание придёт в 3 часа')

def is_user_subscribed(user_id: int) -> bool:
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r') as f:
        user_ids = [int(line.strip()) for line in f.readlines()]
    return user_id in user_ids

def is_user_subscribed1(user_id: int) -> bool:
    if not os.path.exists(USERS_FILE1):
        return False
    with open(USERS_FILE1, 'r') as f:
        user_ids = [int(line.strip()) for line in f.readlines()]
    return user_id in user_ids


async def broadcast(context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
    with open(USERS_FILE1, 'r') as f:
        user_ids = [int(line.strip()) for line in f.readlines()]

    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f'Не удалось отправить сообщение пользователю {user_id}. Ошибка: {e}')

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id in ADMINS_ID:  # Замените YOUR_ADMIN_ID на ваш ID
        message = update.message.text.replace('/broadcast ', '')
        await broadcast(context, message)
    else:
        await update.message.reply_text('У вас нет прав для отправки рассылки.')

async def send_schedule_broadcast(context: ContextTypes.DEFAULT_TYPE, pdf_url: str) -> None:
    with open(USERS_FILE, 'r') as f:
        user_ids = [int(line.strip()) for line in f.readlines()]

    try:
        response = requests.get(pdf_url)
        response.raise_for_status()

        with open('schedule.pdf', 'wb') as f:
            f.write(response.content)

        # Конвертировать PDF в PNG с увеличенным разрешением
        doc = fitz.open('schedule.pdf')
        page = doc.load_page(0)  # Загрузить первую страницу
        zoom = 2  # Увеличить масштаб в 2 раза
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        image_path = 'schedule.png'
        pix.save(image_path)

        for user_id in user_ids:
            try:
                await context.bot.send_photo(chat_id=user_id, photo=open(image_path, 'rb'))
            except Exception as e:
                print(f'Не удалось отправить расписание пользователю {user_id}. Ошибка: {e}')
    except requests.RequestException as e:
        print(f'Не удалось загрузить расписание. Ошибка: {e}')
    except Exception as e:
        print(f'Произошла ошибка при обработке PDF. Ошибка: {e}')
    finally:
        if os.path.exists('schedule.pdf'):
            os.remove('schedule.pdf')
        if os.path.exists('schedule.png'):
            os.remove('schedule.png')

async def send_schedule_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id in ADMINS_ID:  # Замените YOUR_ADMIN_ID на ваш ID
        pdf_url = update.message.text.replace('/send_schedule_broadcast ', '')
        await send_schedule_broadcast(context.application, pdf_url)
    else:
        await update.message.reply_text('У вас нет прав для отправки расписания.')

def main() -> None:
    if not TOKEN:
        raise ValueError("Токен API не установлен. Убедитесь, что переменная окружения TELEGRAM_TOKEN установлена.")

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("broadcast", send_broadcast))
    application.add_handler(CommandHandler("send_schedule_broadcast", send_schedule_broadcast_command))

    # Настройка планировщика
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_schedule_broadcast, CronTrigger(hour=15, minute=0, day_of_week='mon-sat'), args=[application, 'https://rasp.vksit.ru/spo.pdf'])
    scheduler.add_job(send_schedule_broadcast, CronTrigger(hour=15, minute=0, day_of_week='mon-sat'), args=[application, 'https://rasp.vksit.ru/тpo.pdf'])
    scheduler.start()

    application.run_polling()

if __name__ == '__main__':
    main()
