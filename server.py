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
        count = 0

        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if self.login == client.login:
                        count += 1
                if count == 1:
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history()
                else:
                    self.transport.write(
                        f"Логин {self.login} занят, попробуйте другой".encode()
                    )
                    self.transport.close()
                    self.server.clients.remove(self)
                    print(f"Попытка подключения пользователя с существующим логином <{self.login}>")

            else:
                self.transport.write(
                    f"Неправильный логин!\n".encode()
                )

        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}>: {message}"
        self.server.history.append(format_string)
        encoded = format_string.encode()

        for client in self.server.clients:
            client.transport.write(encoded)

    def send_history(self):
        if len(self.server.history) > 0:
            history_str = "History:\n"
            for mes in self.server.history[-10:]:
                 history_str += str(mes)
                 history_str += "\n"
        else:
            history_str = "History is empty\n"

        encoded_mes = history_str.encode()
        self.transport.write(encoded_mes)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print(f"Пришел новый клиент")

    def connection_lost(self, exception):
        if self in self.server.clients:
            self.server.clients.remove(self)
        print(f"Клиент вышел")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
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
