import telebot
import time
import datetime
from mysql.connector import Error
from multiprocessing import *
import schedule
import mysql.connector
from telebot import types
import pandas as pd
import plotly.graph_objs as go
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
               bot.send_message(call.message.chat.id, 'Напишите ваш результат.')
           if call.data == "stat":
               statistic(call.message.chat.id)
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
        if len(message.text) <=3 and int(message.text) <= 100:
            now = datetime.datetime.now()
            try:  # Создаем столбец, название - сегодняшяя дата.
                sql = "ALTER TABLE `users` ADD `{:s}` INT".format(str(now.strftime("%d.%m.%Y")))
                cursor.execute(sql)
                sql = "UPDATE users SET {:s} = (%s) WHERE  user_id = (%s)".format(str(now.strftime("%d.%m.%Y")))
                val = (message.text, message.from_user.id)
                cursor.execute(sql, val)
                bd.commit()
                print("Создаем таблицу этого дня")
                bot.send_message(message.chat.id, "Успешно добавлено ")
            except Exception as e:
                sql = "UPDATE `users` SET `{:s}` = (%s) WHERE  user_id = (%s)".format(str(now.strftime("%d.%m.%Y")))
                val = (message.text, message.from_user.id)
                cursor.execute(sql, val)
                bd.commit()
                bot.send_message(message.chat.id, "Успешно добавлено ")



    except ValueError:
        bot.send_message(message.chat.id, 'Время пишется цифрами')



##################### Закончился блок ,связанный с общением с ботом.



#Блок, связанный с отправкой стистики.
def query_to_bigquery(query):
    cursor.execute(query)
    result = cursor.fetchall()
    temp = [tuple(int(result[0][i]) for i in range(3, len(*result)))]
    cursor.execute("SELECT * FROM `users` WHERE id = '3';")
    tmp = cursor.fetchall()
    temp2 =[tuple(tmp[0][i] for i in range(3, len(*result)))]
    data = [temp2[0], temp[0]]
    dataframe = pd.DataFrame(data, index= ['time', 'res']).T
    return dataframe


def get_and_save_image(id): #Вызывает функцию для сбора данных
    query = "SELECT * FROM `users` WHERE user_id = '{:s}'".format(str(id))
    dataframe = query_to_bigquery(query) # Получение DataFrame
    x = dataframe['time'].tolist()
    y = dataframe['res'].tolist()
    layout = dict(plot_bgcolor='white',
                  margin=dict(t=35, l=20, r=20, b=10),
                  xaxis=dict(title='Дата',
                             range=[-1, 5.5],
                             linecolor='#d9d9d9',
                             showgrid=False,
                             mirror=True),
                  yaxis=dict(title='Результат',
                             range=[0, 100],
                             linecolor='#d9d9d9',
                             showgrid=False,
                             mirror=True))

    data = go.Scatter(x=x,
                      y=y,
                      text=y,
                      textposition='top right',
                      textfont=dict(color='#E58606'),
                      mode='lines+markers+text',
                      marker=dict(color='#5D69B1', size=9),
                      line=dict(color='#52BCA3', width=1, dash='dash'),
                      name='citations')

    fig = go.Figure(data=data, layout=layout)
    fig.update_layout(
        title_text="Статистика"
    )
    fig.write_image("viz.png")


def send_image(id):
    get_and_save_image(id)
    chat_id = id
    bot.send_photo(chat_id=chat_id, photo=open('viz.png', 'rb'))
    print(id + " Понадобилась статистика")


def statistic(id):
    send_image(id)

#Закончился блок со статистикой


if __name__ == '__main__':
    start_process()
    try:
        bot.polling(none_stop=True)
    except:
        pass