import requests
import time
from random import randint
import json
from websocket import create_connection, WebSocketConnectionClosedException
import bottle
import socket


class VKCoin:
    def __init__(self, user_id, key, token=None):
        self.link = 'https://coin-without-bugs.vkforms.ru/merchant/'
        self.method_url = 'https://api.vk.com/method/'
        self.user_id = user_id
        self.key = key
        self.token = token
        self.websocket_handler = None
        self.websocket_url = None
        self.websocket_instance = None
        self.longpoll_handler = None
        self.longpoll_transaction = None
        self.callback_handler = None
        self.callback_port = None

    def _send_api_request(self, method, params):
        response = requests.post(self.link + method, json=params).json()
        if 'error' in response:
            raise Exception(response['error']['message'])
        return response['response']

    def _create_ws_link(self):
        if not self.websocket_url:
            response = requests.get(self.method_url + 'apps.get', params={'access_token': self.token, 'app_id': 6915965,
                                                                          'v': 5.52}).json()
            try:
                self.websocket_url = response['response']['items'][0]['mobile_iframe_url']
            except KeyError:
                raise Exception('Неверный токен')

        user_id = int(self.websocket_url.split('user_id=')[-1].split('&')[0])
        ch = user_id % 32
        self.user_id = user_id
        ws_link = self.websocket_url.replace('https', 'wss').replace('\\', '')
        ws_link = ws_link.replace('index.html', f'channel/{ch}')
        ws_link += f'&ver=1&upd=1&pass={user_id - 1}'
        self.websocket_url = ws_link

    def send_payment(self, to_id, amount, mark_as_merchant=False):
        data = {'merchantId': self.user_id, 'key': self.key, 'toId': to_id, 'amount': amount}
        if mark_as_merchant:
            data['markAsMerchant'] = True
        return self._send_api_request('send', params=data)

    def get_payment_url(self, amount, payload=None, free_amount=False):
        if not payload:
            payload = randint(-2e9, 2e9)
        user_id = '{:x}'.format(self.user_id)
        amount = '{:x}'.format(amount)
        payload = '{:x}'.format(payload)
        link = f'https://vk.com/coin#m{user_id}_{amount}_{payload}'
        if free_amount:
            link += '_1'
        return link

    def get_transactions(self, tx, last_tx=None):
        data = {'merchantId': self.user_id, 'key': self.key, 'tx': tx}
        if last_tx:
            data['lastTx'] = last_tx
        return self._send_api_request('tx', params=data)

    def get_balance(self, *users):
        if len(users) == 0:
            users = [self.user_id]
        data = {'merchantId': self.user_id, 'key': self.key, 'userIds': users}
        return self._send_api_request('score', params=data)

    def set_shop_name(self, name):
        data = {'merchantId': self.user_id, 'key': self.key, 'name': name}
        return self._send_api_request('set', params=data)

    def remove_callback_endpoint(self):
        data = {'merchantId': self.user_id, 'key': self.key, 'callback': None}
        return self._send_api_request('set', params=data)

    def set_callback_endpoint(self, ip=None, port=8080):
        if ip is None:
            ip = 'http://' + socket.gethostbyname(socket.getfqdn()) + ':' + str(port)
            print(ip)
        self.callback_port = port
        data = {'merchantId': self.user_id, 'key': self.key, 'callback': ip}
        return self._send_api_request('set', params=data)

    def callback_server(self):
        data = bottle.request.body.read().decode()
        if self.callback_handler:
            self.callback_handler(json.loads(data))
        return 'OK'

    def get_top(self, top_type='user'):
        if not self.websocket_url:
            self.websocket_url = self._create_ws_link()
        ws = create_connection(self.websocket_url)
        init = json.loads(ws.recv())
        ws.close()
        return init.get('top').get(f'{top_type}Top')

    def run_callback(self):
        bottle.route('/', method='POST')(self.callback_server)
        bottle.run(host='0.0.0.0', port=self.callback_port)

    def payment_handler(self, handler_type=None):
        def decorator(handler):
            if handler_type == 'websocket':
                self.websocket_handler = handler
            elif handler_type == 'longpoll':
                self.longpoll_handler = handler
            elif handler_type == 'callback':
                self.callback_handler = handler
            return handler
        return decorator

    def run_longpoll(self, tx, interval=0.2):
        self.longpoll_transaction = self.get_transactions(tx)
        while True:
            time.sleep(interval)
            current_transaction = self.get_transactions(tx)
            if self.longpoll_transaction[0] != current_transaction[0]:
                new_transaction = current_transaction[0]
                if new_transaction['to_id'] == self.user_id:
                    self.longpoll_transaction = current_transaction
                    if self.longpoll_handler:
                        self.longpoll_handler(new_transaction)

    def run_websocket(self):
        if not self.websocket_url:
            self._create_ws_link()
        self.websocket_instance = create_connection(self.websocket_url)
        while True:
            try:
                message = self.websocket_instance.recv()
                if message.startswith('TR'):
                    amount, user_from, payload = message.split()[1:]
                    payload = self.get_transactions([payload])[0]['payload']
                    data = {'from_id': user_from, 'to_id': self.user_id, 'amount': amount, 'payload': payload}
                    if self.websocket_handler:
                        self.websocket_handler(data)
            except WebSocketConnectionClosedException:
                self.websocket_instance = create_connection(self.websocket_url)
            time.sleep(0.1)

