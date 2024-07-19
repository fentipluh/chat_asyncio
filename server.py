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
    def __init__(self, host=os.getenv('HOST'), port=os.getenv('PORT')):
        self.host = host
        self.port = port
        self.queue = asyncio.Queue()
        self.all_users = {}

    async def write_message(self, writer, msg_bytes):
        try:
            writer.write(msg_bytes)
            await writer.drain()
        except (asyncio.CancelledError, ConnectionResetError) as e:
            logging.error(f"Error in write_message: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in write_message: {e}")

    async def broadcaster(self):
        while True:
            try:
                message = await self.queue.get()
                print(f'{message.strip()}')
                msg_bytes = message.encode()
                tasks = [asyncio.create_task(self.write_message(writer, msg_bytes)) for _, (_, writer) in self.all_users.items()]
                _ = await asyncio.wait(tasks)
            except Exception as e:
                logging.error(f"Error in broadcaster: {e}")

    async def broadcast_message(self, message):
        try:
            await self.queue.put(message)
        except Exception as e:
            logging.error(f"Error in broadcast_message: {e}")

    async def connect_user(self, reader, writer):
        try:
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
        except Exception as e:
            logging.error(f"Error in connect_user: {e}")
            raise

    async def disconnect_user(self, name, writer):
        try:
            writer.close()
            await writer.wait_closed()
            del self.all_users[name]
            await self.broadcast_message(f'{name} покинул чат\n')
        except Exception as e:
            logging.error(f"Error in disconnect_user: {e}")

    async def handle_chat_client(self, reader, writer):
        try:
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
        except Exception as e:
            logging.error(f"Error in handle_chat_client (outer): {e}")

    async def run(self):
        try:
            broadcaster_task = asyncio.create_task(self.broadcaster())
            server = await asyncio.start_server(self.handle_chat_client, self.host, self.port)
            async with server:
                print('Сервер запущен\n')
                await server.serve_forever()
        except Exception as e:
            logging.error(f"Error in run: {e}")


async def main():
    host_address = os.getenv("HOST", '127.0.0.1')
    host_port = os.getenv("PORT", 5000)
    create_logger()
    chat_server = ChatServer(host=host_address, port=host_port)
    await chat_server.run()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.info(f"Сервер завершил работу")
    print("Сервер завершил работу!")
except Exception as e:
    logging.error(f"Unexpected exception: {e}")
    print("Сервер завершил работу с ошибкой!")
