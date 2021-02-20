import telebot
import time
import datetime
from mysql.connector import Error
from multiprocessing import *
import schedule
import mysql.connector
from telebot import types
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

"""
Работающий бот
"""

bot = telebot.TeleBot('1656502971:AAFlJSfiLpEH8t0Eg3GBkQdcgMNlGNtaf5o')
bd = mysql.connector.connect(
    host="localhost",
    user="root",
    password="kit456",
    port="3306",
    database="bot"
)
cursor = bd.cursor()

cursor.execute("SELECT time, user_id FROM users WHERE time != 'NULL'")
row = cursor.fetchall()



def start_process():  # Запуск Process
    p1 = Process(target=P_schedule.start_schedule, args=()).start()


class P_schedule():  # Class для работы с schedule

    def start_schedule():  # Запуск schedule
        ######Параметры для schedule######
        P_schedule.send_message1()
        for x,y in row: # Пробегаемся по БД, и запускаем функцию отправки сообщения
            schedule.every().day.at(x).do(P_schedule.send_message1)


        ##################################

        while True:  # Запуск цикла
            schedule.run_pending()
            time.sleep(1)


    ####Функции для выполнения заданий по времени
    def send_message1():
        for x, y in row: # Проверяет текущее время с тем, что указано в БД
            now = datetime.datetime.now() #Для работы со временем
            if now.strftime("%H:%M") == x:
                bot.send_message(y, 'Эй, пора начинать готовиться к ЕГЭ! ' )

                print("Сработал будильник у " + str(y))

    ################




###Настройки команд telebot######### Общение между ботом и пользователем.


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
   try:
       if call.message:
           if call.data == "time":
               bot.send_message(call.message.chat.id, 'Напишите во сколько отправлять вам уведомления в формате xx:xx.'
                                                      'Например: 21:20 или 09:05')
           if call.data == "new_res":
               bot.send_message(call.message.chat.id,'Скоро будет обновление!!' )
           if call.data == "stat":
               statistic()
   except Exception as e:
       print("No")


@bot.message_handler(commands=['help'])
def start_message(message):
    bot.send_message(message.chat.id, 'Этот бот поможет при подготовке к ЕГЭ')


@bot.message_handler(commands=['start'])
def start_message(message):
    otvet = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton(" Изменить вермя", callback_data='time')
    button2 = types.InlineKeyboardButton(" Добавить результат", callback_data='new_res')
    button3 = types.InlineKeyboardButton(" Показать статистику", callback_data='stat')
    otvet.add(button1, button2, button3)
    bot.send_message(message.chat.id, text='Привет, ты написал боту, который помогает отслеживать результаты подготовки к ЕГЭ. '
                                           'Для того, чтобы узнать на что способен этот бот - напиши /help ' , reply_markup=otvet)
    try:
        sql = "INSERT INTO Users (time,  user_id) VALUES (%s,  %s)"
        val = ('NULL', message.from_user.id)
        cursor.execute(sql, val)
        bd.commit()
        print("Опа, новенький! " + str(message.from_user.id) + " ,Вот он")
    except:
        print("Сообщение от старичков, а именно от "  + str(message.from_user.id))




@bot.message_handler(content_types=['text'])
def message(message):
    try:
        #Проверка сообщения на время.
        if len(message.text) == 5 and 0 <= int(message.text[:2]) < 24 and 0 <= int(message.text[3:]) < 60 and \
                message.text[2] == ':':
            try:
                print("Кто-то решил установить будильник/ Изменить время будильника " + str(message.from_user.id))
                sql = "UPDATE users SET time = (%s) WHERE  user_id = (%s)"
                val = (message.text, message.from_user.id)
                cursor.execute(sql, val)
                bd.commit()
                bot.send_message(message.chat.id, "Ваше время изменено " + message.text)
            except Exception as e:
                print("Проблемы с таблицей")

    except ValueError:
        bot.send_message(message.chat.id, 'Время пишется цифрами')



##################### Закончился блок ,связанный с общением с ботом.

#Блок, связанный с отправкой стистики.
def query_to_bigquery(query):
    cursor.execute(query)
    result = cursor.fetchall()
    dataframe = pd.DataFrame(result, columns= ['user_id', 'time'])
    return dataframe


def visualize_bar_chart(x, x_label, y, y_label, title):
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    index = np.arange(len(x))
    plt.xticks(index, x, fontsize=5, rotation=30)
    plt.bar(index, y)
    return plt


def get_and_save_image(): #Вызывает функцию для сбора данных
    query = """
            SELECT user_id, time FROM users
            """
    dataframe = query_to_bigquery(query) # Получение DataFrame
    x = dataframe['user_id'].tolist()
    y = dataframe['time'].tolist()
    plt = visualize_bar_chart(x=x, x_label='user_id', y=y, y_label='time', title='Test')
    plt.savefig('viz.png')


def send_image():
    get_and_save_image()
    chat_id = '403373517'
    bot.send_photo(chat_id=chat_id, photo=open('viz.png', 'rb'))


def statistic():
    send_image()

#Закончился блок со статистикой


if __name__ == '__main__':
    start_process()
    try:
        bot.polling(none_stop=True)
    except:
        pass