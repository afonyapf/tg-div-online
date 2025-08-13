import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, ReplyKeyboardRemove
from aiogram.filters import Command
import os
from datetime import datetime
import re

# ==== НАСТРОЙКИ ====
import os
# Читаем переменную окружения TELEGRAM_BOT_TOKEN
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    raise ValueError('TELEGRAM_BOT_TOKEN environment variable is required')

# Читаем переменную окружения ADMIN_CHAT_ID
ADMIN_CHAT = os.getenv('ADMIN_CHAT_ID')
if not ADMIN_CHAT:
    raise ValueError('ADMIN_CHAT_ID environment variable is required')
ADMIN_CHAT = int(ADMIN_CHAT)

# Функция санитизации для логов
def sanitize_log_input(text):
    if not text:
        return text
    # Удаляем переносы строк и управляющие символы
    return re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', ' ', str(text))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем логгеры для файлов
general_logger = logging.getLogger('general')
applicants_logger = logging.getLogger('applicants')

# Настройка обработчиков для файлов
general_handler = logging.FileHandler('bot_general.log', encoding='utf-8')
applicants_handler = logging.FileHandler('bot_applicants.log', encoding='utf-8')

# Форматтер для логов
file_formatter = logging.Formatter('%(asctime)s - %(message)s')
general_handler.setFormatter(file_formatter)
applicants_handler.setFormatter(file_formatter)

general_logger.addHandler(general_handler)
applicants_logger.addHandler(applicants_handler)
general_logger.setLevel(logging.INFO)
applicants_logger.setLevel(logging.INFO)

# Список пользователей, подавших заявку
applicants = set()

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище данных пользователя
user_data = {}

# ==== INLINE КНОПКИ ====
start_inline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подать заявку", callback_data="apply")],
    [InlineKeyboardButton(text="Не подходит", callback_data="not_interested")]
])

send_inline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отправить", callback_data="send_form")]
])

# ==== /start ====
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    # Логируем информацию о пользователе для получения chat_id
    logger.info(f"Пользователь {message.from_user.id} (@{sanitize_log_input(message.from_user.username)}) запустил бота")
    
    # Общий лог
    general_logger.info(f"ЗАПРОС: /start от {message.from_user.id} (@{sanitize_log_input(message.from_user.username) or 'None'}) {sanitize_log_input(message.from_user.first_name) or ''} {sanitize_log_input(message.from_user.last_name) or ''}")
    
    text = (
        "Здравствуйте!\n\n"
        "Спасибо, что откликнулись на наше приглашение и проявили интерес к участию "
        "в фокус-группе Divan.Online.\n"
        "Мы подготовили для вас подробные условия участия — отправляем их ниже, "
        "чтобы вы могли спокойно ознакомиться и принять решение.\n\n"
        "С теплом,\nКоманда divan online https://divan.online/"
    )

    # Отправляем текст
    await message.answer(text)
    
    # Отправляем документ
    doc_path = "Условия_участия_психологов_в_фокус_группе.docx"
    if os.path.exists(doc_path):
        try:
            doc = FSInputFile(doc_path)
            await message.answer_document(document=doc)
        except Exception as e:
            logger.error(f"Ошибка отправки документа: {sanitize_log_input(str(e))}")
    
    # Отправляем кнопки
    await message.answer("Выберите:", reply_markup=start_inline_kb)
    
    # Убираем клавиатуру
    await message.answer("", reply_markup=ReplyKeyboardRemove())
    
    # Общий лог ответа
    general_logger.info(f"ОТВЕТ: Отправлен стартовый текст и документ пользователю {message.from_user.id}")

# ==== Команда для получения chat_id ====
@dp.message(Command("id"))
async def get_chat_id(message: types.Message):
    chat_info = (
        f"Ваш chat_id: {message.from_user.id}\n"
        f"Username: @{message.from_user.username or 'Не указан'}\n"
        f"Имя: {message.from_user.first_name or ''} {message.from_user.last_name or ''}"
    )
    await message.answer(chat_info)
    logger.info(f"Chat ID запрос: {sanitize_log_input(chat_info)}")
    
    # Общий лог
    general_logger.info(f"ЗАПРОС: /id от {message.from_user.id} (@{sanitize_log_input(message.from_user.username) or 'None'})")
    general_logger.info(f"ОТВЕТ: Отправлена информация о chat_id пользователю {message.from_user.id}")

# ==== Кнопка "Подать заявку" ====
@dp.callback_query(F.data == "apply")
async def process_apply(callback: types.CallbackQuery):
    user_data[callback.from_user.id] = {"text": ""}
    
    # Добавляем пользователя в список подавших заявку
    applicants.add(callback.from_user.id)
    
    await callback.message.answer(
        "Пожалуйста, укажите:\n1. ФИО\n2. Ссылки на соцсети\n3. Контактные данные\n\n"
        "После ввода данных нажмите кнопку 'Отправить'.",
        reply_markup=send_inline_kb
    )
    await callback.answer("Начинаем заполнение заявки")
    
    # Логирование
    general_logger.info(f"ЗАПРОС: Кнопка 'Подать заявку' от {callback.from_user.id} (@{sanitize_log_input(callback.from_user.username) or 'None'})")
    general_logger.info(f"ОТВЕТ: Отправлена форма заявки пользователю {callback.from_user.id}")
    
    applicants_logger.info(f"НАЧАЛО ЗАЯВКИ: ID={callback.from_user.id}, Username=@{sanitize_log_input(callback.from_user.username) or 'None'}, Имя={sanitize_log_input(callback.from_user.first_name) or ''} {sanitize_log_input(callback.from_user.last_name) or ''}")

# ==== Кнопка "Отправить" ====
@dp.callback_query(F.data == "send_form")
async def process_send(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = user_data.get(user_id, {}).get("text", "").strip()
    
    if not data:
        await callback.message.answer(
            "❌ Вы не заполнили данные для заявки.\n\n"
            "Пожалуйста, напишите:\n"
            "1. ФИО\n"
            "2. Ссылки на соцсети\n"
            "3. Контактные данные\n\n"
            "Затем нажмите 'Отправить' снова.",
            reply_markup=send_inline_kb
        )
        await callback.answer("Заполните данные!")
        return

    # Формируем сообщение для админа
    admin_text = (
        f"📋 Новая заявка на участие в фокус-группе\n\n"
        f"👤 Username: @{callback.from_user.username or 'Не указан'}\n"
        f"👤 Имя: {callback.from_user.first_name or ''} {callback.from_user.last_name or ''}\n\n"
        f"📝 Данные заявки:\n{data}"
    )

    try:
        # Отправляем админу
        await bot.send_message(ADMIN_CHAT, admin_text)
        logger.info(f"Заявка отправлена админу {ADMIN_CHAT}")
        
        # Подтверждаем пользователю
        await callback.message.answer(
            "✅ Спасибо! Ваша заявка успешно отправлена.\n\n"
            "Мы свяжемся с вами в ближайшее время."
        )
        
        # Очищаем данные пользователя
        user_data.pop(user_id, None)
        
        logger.info(f"Заявка от пользователя {user_id} обработана успешно")
        
        # Логирование
        general_logger.info(f"ОТВЕТ: Заявка успешно отправлена от {user_id}")
        applicants_logger.info(f"ЗАЯВКА ОТПРАВЛЕНА: ID={user_id}, Username=@{sanitize_log_input(callback.from_user.username) or 'None'}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки заявки от {user_id}: {sanitize_log_input(str(e))}")
        
        # Сохраняем заявку в лог для ручной обработки
        logger.info(f"Сохраненная заявка: {sanitize_log_input(admin_text)}")
        
        # Подтверждаем пользователю (чтобы он не подумал, что заявка потерялась)
        await callback.message.answer(
            "✅ Спасибо! Ваша заявка принята.\n\n"
            "Мы свяжемся с вами в ближайшее время.\n\n"
            "📞 Контакт для связи: divanonline1@gmail.com"
        )
        
        # Очищаем данные пользователя
        user_data.pop(user_id, None)
        
        # Логирование ошибки
        general_logger.info(f"ОШИБКА: Не удалось отправить заявку от {user_id}")
        applicants_logger.info(f"ОШИБКА ОТПРАВКИ: ID={user_id}, Username=@{sanitize_log_input(callback.from_user.username) or 'None'}")
    
    await callback.answer()

# ==== Кнопка "Не подходит" ====
@dp.callback_query(F.data == "not_interested")
async def process_not_interested(callback: types.CallbackQuery):
    final_text = (
        "Спасибо, что нашли время ознакомиться с нашим предложением и условиями фокус-группы.\n"
        "Мы ценим ваш интерес к платформе Divan.Online и надеемся, что в будущем у нас появится возможность поработать вместе.\n\n"
        "Если формат фокус-группы вам пока не подходит, вы всё равно можете:\n\n"
        "— Размещать свой профиль на платформе и получать клиентов\n"
        "— Принимать участие в отдельных спецпроектах\n"
        "— Получать рассылки с новыми возможностями\n\n"
        "Двери Divan.Online всегда открыты для вас.\n"
        "Если захотите вернуться — напишите нам в любое время.\n\n"
        "С теплом и уважением,\nКоманда Divan.Online\n"
        "Почта: divanonline1@gmail.com"
    )
    await callback.message.answer(final_text)
    await callback.answer("Спасибо за внимание!")
    
    # Логирование
    general_logger.info(f"ЗАПРОС: Кнопка 'Не подходит' от {callback.from_user.id} (@{sanitize_log_input(callback.from_user.username) or 'None'})")
    general_logger.info(f"ОТВЕТ: Отправлено сообщение об отказе пользователю {callback.from_user.id}")

# ==== Сбор данных формы ====
@dp.message(F.text)
async def collect_data(message: types.Message):
    user_id = message.from_user.id
    
    # Общий лог всех текстовых сообщений
    general_logger.info(f"ЗАПРОС: Текст от {user_id} (@{sanitize_log_input(message.from_user.username) or 'None'}): {sanitize_log_input(message.text)}")
    
    # Проверяем, что пользователь в процессе заполнения заявки
    if user_id in user_data:
        prev_text = user_data[user_id].get("text", "")
        
        if prev_text:
            user_data[user_id]["text"] = prev_text + "\n" + message.text
        else:
            user_data[user_id]["text"] = message.text
        
        # Подтверждаем получение данных
        await message.answer(
            "✅ Данные получены!\n\n"
            "Нажмите кнопку 'Отправить' для отправки заявки.",
            reply_markup=send_inline_kb
        )
        
        logger.info(f"Получены данные от пользователя {user_id}")
        
        # Логирование для заявителей
        applicants_logger.info(f"ДАННЫЕ ЗАЯВКИ: ID={user_id}, Username=@{sanitize_log_input(message.from_user.username) or 'None'}, Сообщение: {sanitize_log_input(message.text)}")
        general_logger.info(f"ОТВЕТ: Подтверждение получения данных для {user_id}")
    else:
        # Логируем сообщения от пользователей, которые не подавали заявку
        general_logger.info(f"ОТВЕТ: Нет активной заявки для {user_id}")

# ==== Обработка ошибок ====
@dp.error()
async def error_handler(event, exception):
    logger.error(f"Произошла ошибка: {sanitize_log_input(str(exception))}")
    return True

# ==== Запуск ====
async def main():
    try:
        logger.info("🚀 Запуск бота...")
        
        # Получаем информацию о боте
        me = await bot.get_me()
        logger.info(f"Бот запущен: @{sanitize_log_input(me.username)}")
        logger.info(f"Админ чат: {ADMIN_CHAT}")
        
        # Очищаем webhook на всякий случай
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {sanitize_log_input(str(e))}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {sanitize_log_input(str(e))}")