from environs import Env

from django.core.management.base import BaseCommand
from ssbbot.models import Profile, Stuff


import logging
import random
import os
import uuid
import pyqrcode
#from geopy.distance import geodesic as GD

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)


env = Env()
env.read_env()
TOKEN = env.str('TOKEN')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOICE, QUANTITY, TITLE, SEASONAL, PERIOD, BOOK, SURNAME, CONTACT, PASSPORT, PAYMENT, CONFIRM = range(11)


prices = {
    'Лыжи': {
        '1 неделя': 100,
        '2 недели': 200,
        '3 недели': 300,
        '1 месяц': 300,
        '2 месяца': 600,
        '3 месяца': 900,
        '4 месяца': 1200,
        '5 месяцев': 1500,
        '6 месяцев': 1800,
        },
    'Велосипед': {
        '1 неделя': 150,
        '2 недели': 300,
        '3 недели': 450,
        '1 месяц': 400,
        '2 месяца': 800,
        '3 месяца': 1200,
        '4 месяца': 1600,
        '5 месяцев': 2000,
        '6 месяцев': 2400,
        },
    'Сноуборд': {
        '1 неделя': 100,
        '2 недели': 200,
        '3 недели': 300,
        '1 месяц': 300,
        '2 месяца': 600,
        '3 месяца': 900,
        '4 месяца': 1200,
        '5 месяцев': 1500,
        '6 месяцев': 1800,
        },
    'Колеса': {
        '1 месяц': 200,
        '2 месяца': 400,
        '3 месяца': 600,
        '4 месяца': 800,
        '5 месяцев': 1000,
        '6 месяцев': 1200,
        },
    'Другое': {
        '1': 599,
        '2': 749,
        '3': 899,
        },
}

# БОТ - начало
def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    update.message.reply_text(f'Добрый день, {user.first_name}! '
        '\nЯ помогу вам арендовать личную ячейку для хранения вещей. '
        'Давайте посмотрим адреса складов, чтобы выбрать ближайший!',
                             )
    reply_keyboard = [['ул.Складочная, д. 4'],
                     [ 'ул. Свободы, д. 21'], 
                     ['Волгоградский пр, д. 69/1'],
                     ['Крутицкая наб, д. 11']]

    profile, _ = Profile.objects.get_or_create(external_id=update.message.chat_id)
    logger.info(f'Get profile {profile}')
    profile.username = user.username or ''
    profile.first_name = user.first_name or ''
    profile.save()

    update.message.reply_text('Выберите склад:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                         resize_keyboard=True),
                              )
    return CHOICE


def choice(update: Update, context):
    reply_keyboard = [['Сезонные вещи', 'Другое']]
    user_input = update.effective_message.text
    context.user_data['Склад'] = user_input
    update.message.reply_text('Что хотите хранить?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True,
                                                               one_time_keyboard=True))
    return TITLE

def title(update: Update, context):
    user_input = update.effective_message.text
    context.user_data['Описание'] = user_input
    if user_input == 'Сезонные вещи':
        reply_keyboard = [['Лыжи', 'Сноуборд', 'Велосипед', 'Колеса']]
        update.message.reply_text(
            'Что будем хранить?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return SEASONAL
    if user_input == 'Другое':
        reply_keyboard = [['1','2','3','4','5'],['6','7','8','9','10']]
        update.message.reply_text(
        '''Ок! Стоимость: \n
           599 руб - первый 1 кв.м., далее +150 руб за каждый кв. метр в месяц,\n
            напишите сколько квадратных метров вам нужно (от 1 до 10)''',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                         resize_keyboard=True),
        )
        return QUANTITY

def seasonal(update: Update, context: CallbackContext) -> int:
    user_input = update.effective_message.text
    context.user_data['Описание'] = user_input
    user = update.message.from_user
    logger.info("choice of %s, %s: %s", user.first_name,
                user.id, update.message.text)
    update.message.reply_text(
        'Ок! Cтоимость хранения в неделю/месяц:\n'
        '1 лыжи - 100 р/неделя или 300 р/мес\n'
        'сноуборд - 100 р/неделя или 300 р/мес\n'
        '4 колеса - 200 р/мес\n'
        '1 велосипед - 150 р/ неделя или 400 р/мес\n'
        'Напишите количество вещей для хранения',
        reply_markup=ReplyKeyboardRemove(),
        )
    return QUANTITY

def quantity(update: Update, context):
    user_input = update.effective_message.text
    context.user_data['Количество'] = user_input
    reply_keyboard = [['1 неделя','2 недели','3 недели'],['1 месяц','2 месяца','3 месяца'],
                      ['4 месяца','5 месяцев','6 месяцев']]
    update.message.reply_text(
        'Принято! Выберите период хранения',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                         resize_keyboard=True),
        )
    return PERIOD


def period(update: Update, context):
    user_input = update.effective_message.text
    context.user_data['Период'] = user_input
    reply_keyboard = [['Забронировать']]
    
    storage = context.user_data.get('Склад')
    item = context.user_data.get('Описание')
    quantity = context.user_data.get('Количество')
    period = context.user_data.get('Период')
    total_price = int(quantity) * prices[item][period]
    
    update.message.reply_text(f'Проверьте детали вашего заказа: {storage}\n' 
                                f'вещь - {item}, количество - {quantity}, период - {period}.\n'
                                 f'Стоимость хранения составит: {total_price} руб.\n'
                                 'Бронируем?\n'
                                 'Если передумали - начните сначала, нажав /start',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True,
                                                               one_time_keyboard=True))
    return BOOK

def book(update, context):
    user_input = update.effective_message.text
    if user_input == 'Забронировать':
        profile = Profile.objects.get(external_id=update.message.chat_id)
        print(f'sur {profile.last_name}')
        if not profile.last_name:
            update.message.reply_text(
            text='Напишите, пожалуйста, вашу фамилию.',
        )
            return SURNAME
        else:
            return CONTACT



def add_surname(update, context):
    profile = Profile.objects.get(external_id=update.message.chat_id)
    profile.last_name = update.message.text
    profile.save()
    update.message.reply_text(
        f'Добавлена фамилия: {profile.last_name}',
    )

    update.message.reply_text(
        text='Напишите, пожалуйста, телефон для связи.',
        )
    return CONTACT


def add_contact(update, context):
    profile = Profile.objects.get(external_id=update.message.chat_id)
    profile.contact = update.message.text
    profile.save()
    update.message.reply_text(
        f'Добавлен телефон: {profile.contact}',
    )
    update.message.reply_text(
        text='Напишите, пожалуйста, паспортные данные.',
        )
    return PASSPORT


def add_passport(update, context):
    profile = Profile.objects.get(external_id=update.message.chat_id)
    profile.passport = update.message.text
    profile.save()
    update.message.reply_text(
        f'Добавлен паспорт: {profile.passport}',
    )

    update.message.reply_text(
            text='Напишите, пожалуйста, дату рождения.',
        )
    return PAYMENT


def payment(update, context):
    profile = Profile.objects.get(external_id=update.message.chat_id)
    profile.birthday = update.message.text
    profile.save()
    update.message.reply_text(
        f'Добавлена дата рождения: {profile.birthday}',
    )
    reply_keyboard = [['Оплатить']]
    update.message.reply_text(
        'Для оплаты нажмите конпку ниже',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                         resize_keyboard=True),
        )
    return CONFIRM


def confirm(update, context):
    user_input = update.effective_message.text
    if user_input == 'Оплатить':
        url=pyqrcode.create(update.message.chat_id)
        filename = f'{update.message.chat_id}qr.png'
        url.png(filename,scale=15)
        profile = Profile.objects.get(external_id=update.message.chat_id)
        storage = context.user_data.get('Склад')
        item = context.user_data.get('Описание')
        quantity = context.user_data.get('Количество')
        period = context.user_data.get('Период')
        total_price = int(quantity) * prices[item][period]
        stuff = Stuff.objects.create(
        profile=profile,
        storage=storage,
        description=item,
        quantity=quantity,
        period=period,
        price=total_price,
        code=filename,
        )
        stuff.save()
        

    update.message.reply_text(
            text='Заказ создан и успешно оплачен! Ваш код',
        )
    with open(filename, 'rb') as file:
            context.bot.send_document(chat_id=update.message.chat_id, document=file)
    return CHOICE









#БОТ - команда стоп
def stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.first_name}!')
    return ConversationHandler.END


#БОТ - нераспознанная команда
def unknown(update, context):
    reply_keyboard = [['Сезонные вещи', 'Другое']]
    update.message.reply_text(
        'Извините, не понял, что вы хотели этим сказать, начнем сначала',
        reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        )
    )
    return CHOICE


def error(bot, update, error):
    logger.error('Update "%s" caused error "%s"', update, error)
    return CHOICE



class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        # Create the Updater and pass it your bot's token.
        updater = Updater(TOKEN)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher

        # Add conversation handler with the states CHOICE, TITLE, PHOTO, CONTACT, LOCATION
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                CHOICE: [MessageHandler(Filters.text & ~Filters.command, choice)],
                QUANTITY: [MessageHandler(Filters.text & ~Filters.command, quantity)],
                TITLE: [MessageHandler(Filters.text & ~Filters.command, title)],
                SEASONAL: [MessageHandler(Filters.text & ~Filters.command, seasonal)],
                PERIOD: [MessageHandler(Filters.text & ~Filters.command, period)],
                BOOK: [MessageHandler(Filters.text & ~Filters.command, book)],
                SURNAME: [MessageHandler(Filters.text & ~Filters.command, add_surname)],
                PASSPORT: [MessageHandler(Filters.text & ~Filters.command, add_passport)],
                CONTACT: [MessageHandler(Filters.text & ~Filters.command, add_contact)],
                PAYMENT: [MessageHandler(Filters.text & ~Filters.command, payment)],
                CONFIRM: [MessageHandler(Filters.text & ~Filters.command, confirm)],
                
            },
            fallbacks=[CommandHandler('stop', stop)],
        )

        dispatcher.add_handler(conv_handler)
        dispatcher.add_error_handler(error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
