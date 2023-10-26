import os
import telebot
import phrases as ph
from telebot import types
from google.cloud import speech
import datetime
from datetime import date
import traceback
import mysql.connector
from googletrans import Translator

# API
bot = telebot.TeleBot("**********************************************", parse_mode=None)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '1.json'

# sql initialization
temp_var = []
config = {'user': 'root', 'password': '*******', 'host': '***.***.***.***', 'database': 'audio_to_text'}
cnxn = mysql.connector.connect(**config)
cursor = cnxn.cursor()


# two different content button
def button():
    markup = types.ReplyKeyboardMarkup(True)
    button1 = types.KeyboardButton('Audio to text')
    button2 = types.KeyboardButton('/search')
    button3 = types.KeyboardButton('🇬🇧 Translate text message 🇺🇦')
    markup.row(button1, button2)
    markup.row(button3)
    return markup


def language_button():
    markup2 = types.ReplyKeyboardMarkup(True)
    lang1 = types.KeyboardButton('ukrainian')
    lang2 = types.KeyboardButton('english')
    lang3 = types.KeyboardButton('chinese (traditional)')
    lang4 = types.KeyboardButton('french')
    lang5 = types.KeyboardButton('german')
    lang6 = types.KeyboardButton('italian')
    lang7 = types.KeyboardButton('japanese')
    lang8 = types.KeyboardButton('latin')
    lang9 = types.KeyboardButton('polish')

    markup2.row(lang1, lang2)
    markup2.row(lang3, lang4)
    markup2.row(lang5, lang6)
    markup2.row(lang7, lang8)
    markup2.row(lang9, lang10)
    return markup2


# standard command
@bot.message_handler(commands=['start'])
def start_messages(message):
    if message.chat.type == "private":
        bot.send_message(message.chat.id, f'hi, {message.from_user.first_name}', reply_markup=button())
    elif message.chat.type == "group":
        bot.send_message(message.chat.id, 'I awoke')


@bot.message_handler(commands=['help'])
def help_messages(message):
    if message.chat.type == "private":
        bot.send_message(message.chat.id, 'select one of the available tasks:', reply_markup=button())
    elif message.chat.type == "group":
        bot.send_message(message.chat.id, '''awakening bot - /start
        the bot can respond to certain words
        (*some words*, p)''', parse_mode="Markdown")


# -- SECOND FUNCTION --
@bot.message_handler(commands=['search'])
def search(message):
    msg = bot.send_message(message.chat.id, '*enter the search word:*', parse_mode="Markdown")
    bot.register_next_step_handler(msg, search_text)


# -- try to search user message --
def search_text(message):
    mess = str(message.chat.id)
    bot.send_message(message.chat.id, f'your message that contains - {message.text}')
    executeStr = "SELECT audiotext1 FROM audiotext WHERE telegramuser LIKE '" + mess + "' AND audiotext1 LIKE '%" + message.text + "%'"
    cursor.execute(executeStr)
    out = cursor.fetchall()
    if not out:
        bot.send_message(message.chat.id, '`message with such a search word is currently missing`', parse_mode="Markdown")
    else:
        for row in out:
            bot.send_message(message.chat.id, row)


@bot.message_handler(content_types=['text'])
def text_messages(message):
    if message.chat.type == "private":
        if message.text in ph.hi:
            bot.send_message(message.chat.id, f'hello to you, {message.from_user.first_name}')
        elif message.text in ph.can:
            bot.send_message(message.chat.id, 'we\'re working on that')
        elif message.text in ph.bye:
            bot.send_message(message.chat.id, 'good luck')
        elif message.text == 'Audio to text':
            # -- FIRST FUNCTION --
            bot.send_message(message.chat.id, 'record and send *voice file*', parse_mode="Markdown")

            @bot.message_handler(content_types=['voice'])
            def voice_processing(voice_message):
                open_file(voice_message)
                try:
                    temp_var = transcribe_file(f'new_file.oga', voice_message.from_user.id)
                    bot.send_message(voice_message.from_user.id, temp_var)
                    data = [(voice_message.from_user.id, temp_var, date.today())]
                    query = ("INSERT INTO audiotext (telegramuser, audiotext1, dateaudio) "
                             "VALUES (%s, %s, %s)")
                    cursor.executemany(query, data)
                    cnxn.commit()  # changes to our database
                except Exception:
                    bot.send_message(message.chat.id, '`file conversion error is possible`', parse_mode="Markdown")
                    bot.send_message(message.chat.id, '`try to be clear`', parse_mode="Markdown")

            def open_file(audio_file):
                file_info = bot.get_file(audio_file.voice.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                with open(f'new_file.oga', 'wb') as new_file:
                    new_file.write(downloaded_file)
                return new_file.write

            def transcribe_file(speech_file, id):
                client = speech.SpeechClient()
                with open(speech_file, "rb") as audio_file:
                    content = audio_file.read()
                audio = speech.RecognitionAudio(content=content)

                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                    sample_rate_hertz=48000,
                    language_code='en-US'
                )
                operation = client.long_running_recognize(config=config, audio=audio)
                bot.send_message(id, '_is being converted to text..._', parse_mode="Markdown",
                                 reply_markup=button())
                response = operation.result(timeout=60)

                for result in response.results:
                    return format(result.alternatives[0].transcript.lower())
        elif message.text == '🇬🇧 Translate text message 🇺🇦':
            # -- THIRD FUNCTION --
            def choose_language():
                msg = bot.send_message(message.chat.id, 'select the language to translate the text',
                                       reply_markup=language_button())
                bot.register_next_step_handler(msg, message_for_translate)
                return msg

            def message_for_translate(message):
                target_language = message.text
                msg = bot.send_message(message.chat.id, 'enter the text that you want to translate',
                                       reply_markup=button())
                bot.register_next_step_handler(msg, translate_message, target_language)

            def translate_message(message, translate_mess):
                translator = Translator()
                result = translator.translate(message.text, dest=translate_mess)
                bot.send_message(message.chat.id, result.text)

            choose_language()

    elif message.chat.type == "group":
        if message.text in ph.g_hi:
            bot.send_message(message.chat.id, 'and hello to you to learn more /help')
        elif message.text in ph.g_can:
            bot.send_message(message.chat.id, 'find out the current function /help')
        elif message.text in ph.g_bye:
            bot.send_message(message.chat.id, 'farewell')
        elif message.text.endswith(', p'):
            bot.send_message(message.chat.id, '_I\'m still dummy for such language turns'
                                              'but my creator is already working on it_', parse_mode="Markdown")


# error and time information record
try:
    bot.polling(none_stop=True)
except Exception:
    with open(r'errors.txt', 'a') as error_file:
        now = datetime.datetime.now()
        print(f'error bot:  {traceback.print_exc()}', file=error_file)
        print(f'datetime:  {now.strftime("%d-%m-%Y %H:%M:%S")}\n', file=error_file)
