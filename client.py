import asyncio
import logging
import sys
import os

class ChatClient:
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.reader = None
        self.writer = None

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.server_address, self.server_port)
            print(f'Присоединение к {self.server_address}:{self.server_port}')
        except ConnectionRefusedError:
            logging.error(f"Ошибка подключения: сервер {self.server_address}:{self.server_port} недоступен")
            sys.exit(1)
        except OSError as e:
            logging.error(f"Ошибка подключения: {e}")
            sys.exit(1)

    async def read_messages(self):
        try:
            while True:
                result_bytes = await self.reader.readline()
                response = result_bytes.decode()
                print(response.strip())
        except asyncio.CancelledError:
            logging.info("Чтение сообщений отменено")
        except Exception as e:
            logging.error(f"Ошибка при чтении сообщений: {e}")

    async def write_messages(self):
        try:
            while True:
                message = await asyncio.to_thread(sys.stdin.readline)
                message_bytes = message.encode()
                self.writer.write(message_bytes)
                await self.writer.drain()
                if message.strip() == 'quit':
                    break
        except asyncio.CancelledError:
            logging.info("Отправка сообщений отменена")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщений: {e}")
        finally:
            print('Выход с сервера...')

    async def disconnect(self):
        try:
            print('Отключение от сервера')
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            logging.error(f"Ошибка при отключении: {e}")

    async def run(self):
        await self.connect()
        read_task = asyncio.create_task(self.read_messages())

        await self.write_messages()
        read_task.cancel()

        await self.disconnect()

async def main():
    server_address = os.getenv("HOST", '127.0.0.1')
    server_port = os.getenv("PORT", 5000)
    client = ChatClient(server_address, server_port)
    await client.run()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Клиент завершил работу!")
except Exception as e:
    logging.error(f"Непредвиденная ошибка: {e}")
    print("Клиент завершил работу с ошибкой!")