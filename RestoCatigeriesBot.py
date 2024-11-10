import logging
import requests
import aiohttp
import re
import sqlite3 as sl
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

REG_PHONE_1,REG_CARD_2 = range(2)
con = sl.connect('data.db')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Команда /start для показа кнопки
async def start(update: Update, context) -> int:
    if await whatreg(update.effective_chat.id):
        msg = await update.message.reply_text(
        f"Вы не зарегистррованый пользователь\n")
        context.user_data['messages']=[msg.message_id]
        msg = await update.message.reply_text(
        f"Что бы зарегистрироваться отправьте номер телефона в формате\n"
        f"+7xxxxxxxxxx, без пробелов и букв\n"
        f"Допустимый знак +\n")
        context.user_data['messages'].append(msg.message_id)
        context.user_data['messages'].append(update.message.message_id) 
        return REG_PHONE_1
    else:
        msg = await update.message.reply_text(
        f"Будущее меню\n")
        

async def whatreg(chat_id):
    query ="""SELECT * FROM user WHERE chatID = ?"""
    data = con.execute(query,(chat_id,)).fetchall()
    return True if data == [] else False

async def whatPhoneIIKOCARD(phone):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(use_dns_cache=True)) as session:
        payloadAuth = { "apiLogin": "da51d02fdc8248b9a57f37f0edbdee40" }
        async with session.post('https://api-ru.iiko.services/api/1/access_token', json = payloadAuth) as responseAuth:
            if responseAuth.status == 200:
                dataAuth = await responseAuth.json()
                token = dataAuth.get("token")
            else:
                return True
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
                card = dataClientInfo.get("cards")
                print(card)
                return card
            else:
                return True

async def reg_phone(update: Update, context)-> int:
    phone = update.message.text
    pattern = r"^\+7\d{10}$"
    if(bool(re.match(pattern,phone))):
        phone_test = await whatPhoneIIKOCARD(update.message.text)
        if(phone_test is True):
            keyboard = [[KeyboardButton("start")]]
            reply_start = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
            msg = await update.message.reply_text(
            f"Мы не нашли ваш номер телефона в нашей учетной системе.\n"
            f"Если вы только что зарегистрировали бонусную карту попробуйте повторно загистрироватся через 20 минут\n"
            f"Для повторной регистрации нажмите кнопку Старт\n",reply_markup=reply_start)
            return ConversationHandler.END
        context.user_data['phone']=[update.message.text]
        context.user_data['cards']=[phone_test]
        print(phone_test)
        msg = await update.message.reply_text(
        f"Введите номер карты из приложения без пробелов и букв\n")
        context.user_data['messages'].append(msg.message_id)
        context.user_data['messages'].append(update.message.message_id) 
        return REG_CARD_2
    else:
        msg = await update.message.reply_text(
        f"Выввели номер телфона не веным форматом попробуйте еще раз\n"
        f"отправьте номер телефона в формате\n"
        f"+7xxxxxxxxxx, без пробелов и букв\n"
        f"Допустимый знак +\n")
        context.user_data['messages'].append(msg.message_id)
        return REG_PHONE_1
async def reg_card(update: Update, context)-> int:
    cardUser = update.message.text
    phone = context.user_data['phone']
    cardForIiko = context.user_data['cards']
    flat_list = [item for sublist in cardForIiko for item in sublist]
    print(type(cardForIiko))
    print(cardForIiko)
    print(type(cardUser))
    exists = any(item["track"] == cardUser for item in flat_list)
    if exists:
        query ="""INSERT INTO user 
            (telegramID,chatID,phone,cardNumber)
            VALUES 
            (?,?,?,?)"""
        data =(update.effective_user.id,update.effective_chat.id,phone[0],cardUser)
        con.execute(query,data)
        con.commit()
        msg = await update.message.reply_text(
        f"Вы успешно зарегистрировались в нашем телеграмм боте\n"
        f"Возможности бота 24/7\n"
        f"1.Проверить свой баланс\n"
        f"2.Проверить свой Статус Start,Silver,Gold\n"
        f"3.Уведомления после оплаты заказа\n")
        return await start()
    else:
        keyboard = [[KeyboardButton("start")]]
        reply_start = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
        msg = await update.message.reply_text(
        f"Введенная вами карта не примисанна к данному номеру обратитесь к администратору\n"
        f"Что бы начать повторную регистрацию нажмите start\n",reply_markup=reply_start)
        return ConversationHandler.END
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
    return
# Команда отмены
async def cancel(update: Update, context) -> int:
    msg = await update.message.reply_text("⌛Отмена⌛")
    return ConversationHandler.END

# Основной запуск бота
if __name__ == '__main__':
    application = ApplicationBuilder().token('7640228741:AAEtlva3sghniKy3CPnYCBtn3N_jcV3pKQU').build()
    
    # Обработчик регитсрации
    reg_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            REG_PHONE_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_CARD_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_card)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(reg_conv_handler)
    application.run_polling()
