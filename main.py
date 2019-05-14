#!/usr/bin/python3
"""
Главный файл бота
Подключаем библиотеки
"""
import sys
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import vk_api
import vkcoinc as vkcoin
import mysql.connector
from multiprocessing import Process
import re
import time
import random
import textwrap
from PIL import Image, ImageOps, ImageDraw, ImageFont
import requests
from io import BytesIO
"""
Кастомные классы и функции
"""
from functions import *

"""
Константы/Конфиги
"""
config = {}
exec(open("/home/bot/conf.conf").read(), config)
GROUP_ACCESS_TOKEN = config['vk_group_access_token']
COINS_TOKEN = config['vk_coins_token']
GROUP_ID =config['vk_group_id']
OWNER_ID = config['vk_owner_id']
PROCENT_COUNT = config['procent_count']
DB_HOST = config['db_host']
DB_USER = config['db_user']
DB_PASS = config['db_passwd']
DB_NAME = config['db_name']
merchant = vkcoin.VKCoin(user_id=OWNER_ID, key=COINS_TOKEN)
"""
Клавиатура
"""
keyboard = VkKeyboard()
keyboard.add_button('Банк', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Поставить', color=VkKeyboardColor.PRIMARY)
keyboard.add_line()
keyboard.add_button('Как играть?', color=VkKeyboardColor.POSITIVE)


"""
Classes
"""
class Transactions:
    """
    Класс Transactions
    Предоставляет методы для работы с транзакциями
    """

    def __init__(self, dbconnector):
        self.dbconnector = dbconnector

    def add_transaction(self, from_id, conversation_uid, amount):
        """
        Метод add_transaction
        Добавляет транзикцию в БД
        """
        mycursor = self.dbconnector.cursor()
        sql = "INSERT INTO `transactions` (from_id, conversation_uid, amount, time_create) VALUE (\"%s\",\"%s\",\"%s\",\"%s\")" % (from_id, conversation_uid, amount, time.time())
        mycursor.execute(sql)
        self.dbconnector.commit()
        mycursor.close()
        self.dbconnector.commit()

    def get_current_transactions(self, conversation_uid):
        """
        Метод get_current_transactions
        Возвращает список транзакций в текущей беседе
        """
        mycursor = self.dbconnector.cursor()
        sql = "SELECT * FROM `transactions` WHERE `conversation_uid` = %s" % (conversation_uid)
        mycursor.execute(sql)
        result = mycursor.fetchall()
        mycursor.close()
        self.dbconnector.commit()
        return result

    def get_current_transactions_unique(self, conversation_uid):
        """
        Метод get_current_transactions
        Возвращает список транзакций в текущей беседе
        """
        mycursor = self.dbconnector.cursor()
        sql = "SELECT *, SUM(amount) AS sum_amount FROM transactions WHERE conversation_uid = %s GROUP BY from_id" % (conversation_uid)
        mycursor.execute(sql)
        result = mycursor.fetchall()
        mycursor.close()
        self.dbconnector.commit()
        return result

    def get_current_bank(self, conversation_uid):
        """
        Метод get_current_bank
        Возвращает общий банк транзицкий в заданной беседе по uid
        """
        mycursor = self.dbconnector.cursor()
        sql = "SELECT `amount` FROM `transactions` WHERE `conversation_uid` = %s" % (conversation_uid)
        mycursor.execute(sql)
        result = mycursor.fetchall()
        mycursor.close()
        self.dbconnector.commit()

        bank = 0
        for i in result:
            bank += int(i[0])

        return bank

    def trans_dict_img(self, trans_dict, vk):
        user_ids = []
        for i in trans_dict[0:4]:
            count = "+%s" % (digit(round(int(i['count'])/1000)))
            time_left = beautiful_time(round(i['seconds_left']))
            user_ids.append([i['from_id'], count, time_left])
        background = Image.open('/home/bot/images/win_background.png')
        for num, i in enumerate(user_ids, 1):
            # Загружаем картинку с ВК
            user_data = vk.users.get(user_ids=i[0], fields="photo_max")
            response = requests.get(user_data[0]['photo_max'])
            watermark = Image.open(BytesIO(response.content)).convert("RGBA")
            watermark.save("/home/bot/images/watermark.png")

            # Скругляем
            im = Image.open('/home/bot/images/watermark.png')
            im = im.resize((150, 150));
            bigsize = (im.size[0] * 3, im.size[1] * 3)
            mask = Image.new('L', bigsize, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + bigsize, fill=255)
            mask = mask.resize(im.size, Image.ANTIALIAS)
            im.putalpha(mask)
            output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
            output.putalpha(mask)
            output.save('/home/bot/images/output.png')

            # Накладываем текста

            draw = ImageDraw.Draw(background)

            # Накладываем на фон
            if num == 1:
                background.paste(im, (240, 260), im)

                # Имя
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
                name = user_data[0]['first_name'] + " " + user_data[0]['last_name']
                color = 'rgb(51, 51, 51)'  # name color
                draw.text((431, 280), name.upper(), fill=color, font=font)

                # Савка
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
                color = 'rgb(192,192,192)'  # name color
                draw.text((431, 315), i[1], fill=color, font=font)

                # Время
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Light.ttf', size=32)
                color = 'rgb(192,192,192)'  # name color
                draw.text((431, 350), "только что", fill=color, font=font)


            elif num == 2:
                background.paste(im, (240, 430), im)

                font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
                name = user_data[0]['first_name'] + " " + user_data[0]['last_name']
                color = 'rgb(51, 51, 51)'  # name color
                draw.text((431, 450), name.upper(), fill=color, font=font)

                # Савка
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
                color = 'rgb(192,192,192)'  # name color
                draw.text((431, 485), i[1], fill=color, font=font)

                # Время
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Light.ttf', size=32)
                color = 'rgb(192,192,192)'  # name color
                draw.text((431, 520), i[2], fill=color, font=font)

            elif num == 3:
                background.paste(im, (240, 600), im)

                font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
                name = user_data[0]['first_name'] + " " + user_data[0]['last_name']
                color = 'rgb(51, 51, 51)'  # name color
                draw.text((431, 620), name.upper(), fill=color, font=font)

                # Савка
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
                color = 'rgb(192,192,192)'  # name color
                draw.text((431, 655), i[1], fill=color, font=font)

                # Время
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Light.ttf', size=32)
                color = 'rgb(192,192,192)'  # name color
                draw.text((431, 690), i[2], fill=color, font=font)

            elif num == 4:
                background.paste(im, (240, 770), im)

                font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
                name = user_data[0]['first_name'] + " " + user_data[0]['last_name']
                color = 'rgb(51, 51, 51)'  # name color
                draw.text((431, 790), name.upper(), fill=color, font=font)

                # Савка
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
                color = 'rgb(192,192,192)'  # name color
                draw.text((431, 825), i[1], fill=color, font=font)

                # Время
                font = ImageFont.truetype('/home/bot/fonts/Roboto-Light.ttf', size=32)
                color = 'rgb(192,192,192)'  # name color
                draw.text((431, 860), i[2], fill=color, font=font)

        background.save('/home/bot/images/overlap.png')

        photo_upload_url = vk.photos.getMessagesUploadServer()['upload_url']
        request = requests.post(photo_upload_url, files={'photo': open('/home/bot/images/overlap.png', "rb")})
        params = {'server': request.json()['server'],
                  'photo': request.json()['photo'],
                  'hash': request.json()['hash']}
        photo_id = vk.photos.saveMessagesPhoto(**params)[0]['id']
        return photo_id

    def transactions_to_dict(self, trans_data):
        """
        Метод transactions_to_dict
        Возвращает список транзакций в текущей беседе в виде словаря
        """
        # Подсчитываем банк
        bank_count = 0

        for i in trans_data:
                try:
                    bank_count = bank_count + int(i[5])
                except:
                    bank_count = bank_count + int(i[3])

        # Получаем в процентах взнос каждого
        bank_data = []
        for i in trans_data:
            try:
                a = int(i[5]) / bank_count * 100
            except:
                a = int(i[3]) / bank_count * 100

            b = time.time() - float(i[4])

            # Если переданы сумма уникальных транзикций
            try:
                bank_data.append({'conversation_uid': i[2], 'from_id': i[1], 'procent': round(a, 1), 'count': int(i[5]), 'seconds_left': b})
                bank_data = sorted(bank_data, key=lambda i: i['count'], reverse=True)
            except:
                bank_data.append({'conversation_uid': i[2], 'from_id': i[1], 'procent': round(a, 1), 'count': i[3], 'seconds_left': b})
                bank_data = sorted(bank_data, key=lambda i: i['seconds_left'], reverse=False)

        return bank_data

class Conversations:
    """
    Класс Conversations
    Предоставляет методы для работы с беседами
    """
    def __init__(self, dbconnector):
        self.dbconnector = dbconnector

    def get_winner_img(self, id, vk):

        background = Image.open('/home/bot/images/winner_background.png')
        # Загружаем изображение
        user_data = vk.users.get(user_ids=id, fields="photo_max")
        name = (user_data[0]['first_name'] + " " + user_data[0]['last_name'])
        photo = user_data[0]['photo_max']
        response = requests.get(photo)
        watermark = Image.open(BytesIO(response.content)).convert("RGBA")
        watermark.save("/home/bot/images/watermark2.png")

        # Скругляем
        im = Image.open('/home/bot/images/watermark2.png')
        im = im.resize((200, 200));
        bigsize = (im.size[0] * 3, im.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(im.size, Image.ANTIALIAS)
        im.putalpha(mask)
        output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
        output.putalpha(mask)
        output.save('/home/bot/images/output2.png')

        background.paste(im, (400, 450), im)

        font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', size=32)
        color = 'rgb(51, 51, 51)'  # name color

        # Накладываем текст

        para = textwrap.wrap(name, width=15)

        MAX_W, MAX_H = 1000, 1000
        draw = ImageDraw.Draw(background)
        font = ImageFont.truetype('/home/bot/fonts/Roboto-Medium.ttf', 24)

        current_h, pad = 680, 10
        for line in para:
            w, h = draw.textsize(line, font=font)
            draw.text(((MAX_W - w) / 2, current_h), line, fill=color, font=font)
            current_h += h + pad


        background.save('/home/bot/images/overlap2.png')
        photo_upload_url = vk.photos.getMessagesUploadServer()['upload_url']
        request = requests.post(photo_upload_url, files={'photo': open('/home/bot/images/overlap2.png', "rb")})
        params = {'server': request.json()['server'],
                  'photo': request.json()['photo'],
                  'hash': request.json()['hash']}
        photo_id = vk.photos.saveMessagesPhoto(**params)[0]['id']
        return photo_id

    def get_conversation_id(self, id):
        """
        Метод get_conversation_id
        Возвращает conversation_id беседы
        """
        mycursor = self.dbconnector.cursor()
        sql = "SELECT `conversation_id` FROM `conversations` WHERE `id` = %s" % (id)
        mycursor.execute(sql)
        result = mycursor.fetchone()[0]
        mycursor.close()
        self.dbconnector.commit()
        return result

    def get_conversation_uid(self, conversation_id):
        """
        Метод get_conversation_uid
        Возвращает conversation_uid беседы
        """
        mycursor = self.dbconnector.cursor()
        sql = "SELECT `id` FROM `conversations` WHERE `conversation_id` = %s" % (conversation_id)
        mycursor.execute(sql)
        result = mycursor.fetchone()[0]
        mycursor.close()
        self.dbconnector.commit()
        return result

    def get_all_conversations_uids(self):
        """
        Метод get_all_conversations_uids
        Возвращает все conversation_uid'ы беседы
        """
        mycursor = self.dbconnector.cursor()
        sql = "SELECT `id` FROM `conversations`"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        self.dbconnector.commit()
        mycursor.close()

        list = []
        for i in result:
            list.append(i[0])

        return list

    def get_min_rate(self, conversation_id, factor=1):
        """
        Метод get_min_rate
        Возвращает минимальную ставку в беседе
        """
        mycursor = self.dbconnector.cursor()
        sql = "SELECT `min_rate` FROM `conversations` WHERE `conversation_id` = %s" % (conversation_id)
        mycursor.execute(sql)
        result = mycursor.fetchone()[0]*factor
        mycursor.close()
        self.dbconnector.commit()
        return result

    def get_status(self, conversation_id):
        """
        Метод get_status
        Возвращает True если беседа существует в БД
        """
        mycursor = self.dbconnector.cursor()
        sql = "SELECT `id` FROM `conversations` WHERE `conversation_id` = %s" % (conversation_id)
        mycursor.execute(sql)
        result = mycursor.fetchone()
        mycursor.close()
        self.dbconnector.commit()
        if(result):
            return True
        else:
            return False

    def add_conversation(self, conversation_id):
        """
        Метод add_converstaion
        Добавляет беседу в БД
        """
        mycursor = self.dbconnector.cursor()
        sql = "INSERT INTO `conversations` (conversation_id) VALUE (\"%s\")" % (conversation_id)
        mycursor.execute(sql)
        self.dbconnector.commit()
        mycursor.close()

    def set_min_rate(self, min_rate, conversation_id):
        """
        Метод set_min_rate
        Устанавливает минимальную ставку
        """
        mycursor = self.dbconnector.cursor()
        sql = "UPDATE `conversations` SET `min_rate` = '%s' WHERE `conversation_id` = %s" % (min_rate, conversation_id)
        mycursor.execute(sql)
        self.dbconnector.commit()
        mycursor.close()


def core():
    """
    Подключение к базе данных MySQL
    """
    dbconnector = mysql.connector.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, database=DB_NAME)
    """
    Подключение к мерчанту VK Coins
    """
    #merchant = vkcoin.VKCoinApi(user_id=OWNER_ID, key=COINS_TOKEN)
    """
    Подключение к ВК
    """
    vk_session = vk_api.VkApi(token=GROUP_ACCESS_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, group_id=GROUP_ID)
    while True:
        try:
            for event in longpoll.listen():

                if (event.type == VkBotEventType.MESSAGE_NEW):
                        
                    conv = Conversations(dbconnector)
                    trans = Transactions(dbconnector)
                    # Если это сообщение, то получаем переменные беседы
                    conversation_id = int(event.object.peer_id)
                    
                    if(event.object.peer_id == event.object.from_id):
                        message = "Привет! Игры проходят в нашей беседе:\nhttps://vk.me/join/AJQ1d1FoRBBpa69EiL1I2i2R"
                        vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message=message)
                        exit()
                    
                    if conv.get_status(conversation_id):

                        conversation_uid = conv.get_conversation_uid(conversation_id)

                        if "банк" in event.object.text.lower():

                            # Получаем все транзикции и формируем сообщение
                            trans_data = trans.get_current_transactions_unique(conversation_uid)

                            if trans_data:

                                trans_dict = trans.transactions_to_dict(trans_data)
                                message = "Сейчас в банке %s коинов\n\nВ текущем розыгрыше участвуют:\n" % (digit(round(trans.get_current_bank(conversation_uid) / 1000)))
                                for i in trans_dict:
                                    name = beautiful_name(i['from_id'], vk, False)
                                    message += "%s - %s коинов (%s%%)\n" % (name, digit(round(i['count'] / 1000)), i['procent'])
                                message += "\nБанк разыгрывается каждые 5 минут"
                            else:
                                message = "Сейчас в банке 0 коинов\n\nСтавки отсутствуют :(\n\nБанк разыгрывается каждые 5 минут"


                            vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message=message)

                        elif "поставить" in event.object.text.lower():
                            # Получаем ссылку для оплаты, для текущей беседы
                            message = "Сделать ставку можно по ссылке в приложении: %s\nМинимальная ставка в этой беседе: %s" % (merchant.get_payment_url(amount=conv.get_min_rate(conversation_id, 1), payload=conversation_uid, free_amount=True), digit(round(conv.get_min_rate(conversation_id, 1)/1000)))
                            vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message=message)

                        elif "как играть" in event.object.text.lower():
                            vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message="Привет! Вся информация есть в закрепленном сообщении, обязательно посмотри! Там написаны все правила! ")


                        elif "минимальная ставка" in event.object.text.lower():
                            if int(event.object.from_id) == int(OWNER_ID):
                                try:
                                    new_min_rate = int(''.join(filter(str.isdigit, event.object.text.lower())))
                                    conv.set_min_rate(new_min_rate*1000, conversation_id)
                                    vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message="Новая минимальная для этой комнаты: %s" % round(new_min_rate))
                                except:
                                    vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message="Ошибка установки минимальной ставки, пример правильного ввода: 'минимальная ставка 5000'")											
                    else:
                        conv.add_conversation(conversation_id)
                        message = "Новая комната инициализирована!\nУстановлена дефолтная минимальная ставка: %s\nКоманда для установки минимальной ставки: 'минимальная ставка (число)'\nКоманда доступна только для *id%s (администратора)." % (digit(round(conv.get_min_rate(conversation_id, 1)/1000)), OWNER_ID)
                        vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message=message)
        except:
            # Переподключение в случае обрыва соединения с ВК
            print("Revival of the connection to VK ~")
            continue

def eye():
    """
    Подключение к базе данных MySQL
    """
    dbconnector = mysql.connector.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, database=DB_NAME)
    """
    Подключение к мерчанту VK Coins
    """
    #merchant = vkcoin.VKCoin(user_id=OWNER_ID, key=COINS_TOKEN)  # Ваш ID и ключ
    """
    Подключение к ВК
    """
    vk_session = vk_api.VkApi(token=GROUP_ACCESS_TOKEN)
    vk = vk_session.get_api()
    while True:
        try:
            @merchant.payment_handler(handler_type='callback')
            def payment_received(data):
                print("============================")
                print("NEW PAYMENT")
                print(data)
                print("============================")
                from_id = data['from_id']
                amount = data['amount']
                payload = data['payload']

                # Создаем экземпляр класса бесед и получаем ид текущей беседы для отправки сообщения
                conv = Conversations(dbconnector)
                conversation_id = conv.get_conversation_id(payload)
                min_rate = int(conv.get_min_rate(conversation_id))
                if (int(amount) < min_rate):
                    pass
                else:
                    # Если сумма в транзикции больше или равна минимальной ставки в беседе
                    # Создаем экземпляр класса транзакций
                    trans = Transactions(dbconnector) # payload выступает в качестве ида беседы
                    # Добавляем новую транзакцию
                    trans.add_transaction(from_id, payload, amount)

                    # Получаем все транзикции и формируем сообщение
                    trans_data = trans.get_current_transactions(payload)
                    trans_dict = trans.transactions_to_dict(trans_data)
                    name = beautiful_name(trans_dict[0]['from_id'], vk)
                    message = "Новый перевод в банк от %s" % (name)

                    attachment_data = 'photo-%s_%s' % (GROUP_ID, trans.trans_dict_img(trans_dict, vk))

                    vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message=message, attachment=attachment_data)

            merchant.set_callback_endpoint()
            merchant.run_callback()
        
        except:
            print("\nPayment error!\n")
            continue

def croupier():
    """
    Подключение к базе данных MySQL
    """
    dbconnector = mysql.connector.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, database=DB_NAME)
    """
    Подключение к мерчанту VK Coins
    """
    #merchant = vkcoin.VKCoinApi(user_id=OWNER_ID, key=COINS_TOKEN)
    """
    Подключение к ВК
    """
    vk_session = vk_api.VkApi(token=GROUP_ACCESS_TOKEN)
    vk = vk_session.get_api()
    conv = Conversations(dbconnector)
    trans = Transactions(dbconnector)

    while True:
        # Получаем список uids всех бесед
        conversations_uids = conv.get_all_conversations_uids()

        # Определяем уникальные беседы в которых есть хотя бы 2 ставки
        unique_conversations = []
        for i in conversations_uids:
            mycursor = dbconnector.cursor()
            sql = "SELECT COUNT(DISTINCT from_id) FROM `transactions` WHERE `conversation_uid` = %s" % (i)
            mycursor.execute(sql)
            result = mycursor.fetchone()[0]
            if result >= 2:
                unique_conversations.append(i)
            mycursor.close()

        # Если есть уникальные беседы, то повышаем им прошедшее минуты на 1
        if unique_conversations:
            str_unique_conversations = convert_list_to_str(unique_conversations)
            mycursor = dbconnector.cursor()
            sql = "UPDATE `conversations` SET `minutes_left` = `minutes_left` + 1 WHERE `id` IN (%s)" % (str_unique_conversations)
            mycursor.execute(sql)
            dbconnector.commit()
            mycursor.close()

        # Получаем uid'ы бесед у которых прошло 5 минут
        mycursor = dbconnector.cursor()
        sql = "SELECT id FROM `conversations` WHERE `minutes_left` >= 5"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        mycursor.close()
        conversations_left = []
        for i in result:
            conversations_left.append(i[0])

        # Выбираем победителя в беседах у которых прошло 5 минут
        if conversations_left:
            for x in conversations_left:
                # Получаем список словарей участников каждой беседы, у которой прошло 5 минут
                transactions_left_dict = trans.transactions_to_dict(trans.get_current_transactions_unique(x))

                # Получаем conversation_id текущей беседы
                conversation_id = conv.get_conversation_id(x)
                
                win_bank = trans.get_current_bank(x)
                
                # Удаляем транзикции, все транзикции пришедшее после этого момента, попадут в след розыгрыш
                str_conversations_left = convert_list_to_str(conversations_left)
                mycursor = dbconnector.cursor()
                sql = "DELETE FROM `transactions` WHERE `conversation_uid` IN (%s)" % (str_conversations_left)
                mycursor.execute(sql)
                dbconnector.commit()
                mycursor.close()
                
                # Выбираем победителя
                procents_list = []
                for i in transactions_left_dict:
                    procents_list.append(int(i['procent']))
                user_win = random.choices(transactions_left_dict, weights=procents_list)
                win_bank = {'win_bank':win_bank}
                user_win[0].update(win_bank)

                # Отнимаем процент от куша
                services_procent = round((user_win[0]['win_bank'] - user_win[0]['count'])/PROCENT_COUNT)
                user_win[0]['win_bank'] -= services_procent

                name = beautiful_name(user_win[0]['from_id'], vk)

                message = "Начинаем выбор победителя, который заберет банк в %s коинов...\n" % (
                digit(round(user_win[0]['win_bank'] / 1000)))
                vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message=message)
                time.sleep(10)

                attachment_data = 'photo-%s_%s' % (GROUP_ID, conv.get_winner_img(user_win[0]['from_id'], vk))

                # Отправляем коины победителю
                print("============================")
                print("Send %s coins to winner %s" % (user_win[0]['win_bank'], user_win[0]['from_id']))
                result = merchant.send_payment(user_win[0]['from_id'], user_win[0]['win_bank'])
                print(result)
                print("============================")

                message = "Приз забирает %s, вложивший %s коинов!" % (name, digit(round(user_win[0]['count'] / 1000)))
                vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message=message, attachment=attachment_data)
                vk.messages.send(peer_id=conversation_id, random_id=get_random_id(), keyboard=keyboard.get_keyboard(), message= "У вас не осталось койнов? Хочется быть круче остальных? Тогда тебе к нам! \n Низкие и доступные цены! \n Всё автоматически!\n Заходи сюда -> *everyshopvkc(Every Shop)")

        # Сбиваем на 0 прошедшие минуты беседам, у которых прошло 5 минут.
        mycursor = dbconnector.cursor()
        sql = "UPDATE `conversations` SET `minutes_left` = 0 WHERE `minutes_left` >= 5"
        mycursor.execute(sql)
        dbconnector.commit()
        mycursor.close()
        time.sleep(60)


"""
Главная точка входа в скрипт. Ядро (core) бота работает параллельно с (eye), который отслеживает транзакции коинов.
"""
if __name__ == '__main__':
    Process(target=core).start()
    Process(target=eye).start()
    Process(target=croupier).start()