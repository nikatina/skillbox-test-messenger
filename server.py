"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):

        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                if self.login not in self.server.logins:
                    self.server.logins.append(self.login)
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history()
                else:
                    self.server.logins.append(self.login)
                    self.transport.write(
                        f"Логин {self.login} занят, попробуйте другой".encode()
                    )
                    self.server.clients.remove(self)
                    print("Попытка подключения пользователя с существующим логином")
            else:
                self.transport.write(
                    f"Введите логин!".encode()
                )

        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}>: {message}"
        self.server.history.append(format_string)
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        history_str = "History:\n"
        for mes in self.server.history[-10:]:
             history_str += str(mes)
             history_str += "\n"
        encoded_mes = history_str.encode()

        for client in self.server.clients:
            if client.login == self.login:
                client.transport.write(encoded_mes)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        if self in self.server.clients:
            self.server.clients.remove(self)
        print("Соединение разорвано")
        if self.login in self.server.logins:
            self.server.logins.remove(self.login)


class Server:
    clients: list
    logins: list
    history: list

    def __init__(self):
        self.clients = []
        self.logins = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
