import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

GET_CATEGORIES, EXIT_CATEGORIES = range(2)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Команда /start для показа кнопки
async def start(update: Update, context) -> int:
    msg = await update.message.reply_text("Введите номер телефона")
    context.user_data['messages'] = [msg.message_id, update.message.message_id]
    return GET_CATEGORIES

async def get_categories(update: Update, context) -> int:
    msg = await update.message.reply_text("⌛ Запрос в базу данных ⌛")
    context.user_data['phone'] = update.message.text  # Сохраняем номер телефона как строку
    context.user_data['messages'].append(update.message.message_id)
    context.user_data['messages'].append(msg.message_id)
    return EXIT_CATEGORIES

async def exit_categories(update: Update, context) -> int:
    logging.info("Переход в состояние EXIT_CATEGORIES")
    print("asdasdasdasdsad")
    phone = context.user_data['phone']
    try:
        categories = await iikoTransport(phone)  # Используем асинхронную функцию
        print(categories)
    except KeyError :  
        print("kall")
    msg = await update.message.reply_text(f"Ваши категории: {categories}")
    context.user_data['messages'].extend([msg.message_id, update.message.message_id])

    # Удаляем все сообщения
    for message_id in context.user_data['messages']:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение {message_id}: {e}")

    context.user_data.clear()
    return ConversationHandler.RESTART  # Перезапуск диалога

async def iikoTransport(phone: str) -> list:
    payloadAuth = {
        "apiLogin": "da51d02fdc8248b9a57f37f0edbdee40"
    }
    responseAuth = requests.post('https://api-ru.iiko.services/api/1/access_token', json=payloadAuth)
    
    if responseAuth.status_code == 200:
        dataAuth = responseAuth.json()
        token = dataAuth.get("token")
    else:
        print("Ошибка авторизации:", responseAuth.status_code)
        return ["Ошибка авторизации"]
    payloadClientInfo = {
        "phone": phone,
        "type": "phone",
        "organizationId": "5f172cf0-d387-4ec2-b3b6-578a8126b083"
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    responseClientInfo = requests.post('https://api-ru.iiko.services/api/1/loyalty/iiko/customer/info', json=payloadClientInfo, headers=headers)
    
    if responseClientInfo.status_code == 200:
        dataClientInfo = responseClientInfo.json()
        return dataClientInfo.get("categories", ["Категории не найдены"])
    else:
        print("Ошибка получения данных клиента:", responseClientInfo.json())
        return ["Ошибка получения данных"]

# Команда отмены
async def cancel(update: Update, context) -> int:
    context.user_data['messages'].append(update.message.message_id)
    for message_id in context.user_data['messages']:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение {message_id}: {e}")
    
    keyboard = [[KeyboardButton("Отчет")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text("Отчет отменен. Нажмите Отчет для нового отчета.", reply_markup=reply_markup)
    context.user_data.clear()
    return ConversationHandler.END

# Основной запуск бота
if __name__ == '__main__':
    application = ApplicationBuilder().token('7640228741:AAEtlva3sghniKy3CPnYCBtn3N_jcV3pKQU').build()
    
    # Определение ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_categories)],
            EXIT_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, exit_categories)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()
