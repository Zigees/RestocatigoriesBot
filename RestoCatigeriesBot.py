import logging
import requests
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

GET_CATEGORIES = range(1)

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
    phone = update.message.text  # Сохраняем номер телефона как строку
    msg = await update.message.reply_text("⌛ Запрос в базу данных ⌛")
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(use_dns_cache=True)) as session:
        payloadAuth = { "apiLogin": "da51d02fdc8248b9a57f37f0edbdee40" }
        async with session.post('https://api-ru.iiko.services/api/1/access_token', json = payloadAuth) as responseAuth:
            if responseAuth.status == 200:
                dataAuth = await responseAuth.json()
                token = dataAuth.get("token")
                if not token:
                    await msg.edit_text("Не удалось получить токен.")
                    return ConversationHandler.END
            else:
                await msg.edit_text("Ошибка при получении токена.")
                return ConversationHandler.END
        headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",}
        payloadClientInfo = {
        "phone": phone,
        "type": "phone",
        "organizationId": "5f172cf0-d387-4ec2-b3b6-578a8126b083"} 
        async with session.post('https://api-ru.iiko.services/api/1/loyalty/iiko/customer/info', json=payloadClientInfo ,headers=headers) as responseClientInfo:
            if responseClientInfo.status == 200:
                dataClientInfo = await responseClientInfo.json()
                categories = dataClientInfo.get("categories")
                if not categories:
                    await msg.edit_text("Не удалось получить токен.")
                    return ConversationHandler.END
            else:
                await msg.edit_text("Ошибка при получении токена.")
                return ConversationHandler.END
        categoriesList= [category['name'] for category in categories]
        categoriesText = "\n".join(categoriesList)
    await  msg.edit_text(
        f"Ваш телефон: {phone}"
        f"Ваши категории: {categoriesText}")
    context.user_data['messages'].append(update.message.message_id)
    context.user_data['messages'].append(msg.message_id)
    return ConversationHandler.END
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
            GET_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_categories)]
            # EXIT_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, exit_categories)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()
