import asyncio
import os
import logging
import json

def create_logger():
    file_handler = logging.FileHandler('logs.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

class ChatServer:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.queue = asyncio.Queue()
        self.all_users = {}

    async def write_message(self, writer, msg_bytes):
        writer.write(msg_bytes)
        await writer.drain()

    async def broadcaster(self):
        while True:
            message = await self.queue.get()
            print(f'{message.strip()}')
            msg_bytes = message.encode()
            tasks = [asyncio.create_task(self.write_message(writer, msg_bytes)) for _, (_, writer) in self.all_users.items()]
            _ = await asyncio.wait(tasks)

    async def broadcast_message(self, message):
        await self.queue.put(message)

    async def connect_user(self, reader, writer):
        writer.write('Введите своё имя:\n'.encode())
        await writer.drain()
        name_bytes = await reader.readline()
        name = name_bytes.decode().strip()
        self.all_users[name] = (reader, writer)

        await self.broadcast_message(f'{name} присоединился к чату \n')
        welcome = f'Добро пожаловать, {name}! Введите "quit" для выхода из чата!.\n'
        writer.write(welcome.encode())
        await writer.drain()
        return name

    async def disconnect_user(self, name, writer):
        writer.close()
        await writer.wait_closed()
        del self.all_users[name]
        await self.broadcast_message(f'{name} покинул чат\n')

    async def handle_chat_client(self, reader, writer):
        name = await self.connect_user(reader, writer)
        logging.info(json.dumps({"event": "join", "login": name}, ensure_ascii=False))
        try:
            while True:
                line_bytes = await reader.readline()
                line = line_bytes.decode().strip()
                if line:
                    logging.info(json.dumps({"event": "message", "text": line, "login": name}, ensure_ascii= False))
                if line == 'quit':
                    logging.info(json.dumps({"event": "leave", "login": name}, ensure_ascii= False))
                    break
                await self.broadcast_message(f'{name}: {line}\n')
        finally:
            await self.disconnect_user(name, writer)

    async def run(self):
        broadcaster_task = asyncio.create_task(self.broadcaster())
        server = await asyncio.start_server(self.handle_chat_client, self.host, self.port)
        async with server:
            print('Сервер запущен\n')
            await server.serve_forever()


async def main():
    host_address = os.getenv("HOST", '127.0.0.1')
    host_port = os.getenv("PORT", 8888)
    create_logger()
    chat_server = ChatServer(host=host_address, port=host_port)
    await chat_server.run()

asyncio.run(main())
