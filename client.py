import asyncio
import sys
import os
class ChatClient:
    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.server_address, self.server_port)
        print(f'Присоединение к {self.server_address}:{self.server_port}')

    async def read_messages(self):
        while True:
            result_bytes = await self.reader.readline()
            response = result_bytes.decode()
            print(response.strip())

    async def write_messages(self):
        while True:
            message = await asyncio.to_thread(sys.stdin.readline)
            message_bytes = message.encode()
            self.writer.write(message_bytes)
            await self.writer.drain()
            if message.strip() == 'quit':
                break
        print('Выход с сервера...')

    async def disconnect(self):
        print('Отключение от сервера')
        self.writer.close()
        await self.writer.wait_closed()

    async def run(self):
        await self.connect()
        read_task = asyncio.create_task(self.read_messages())

        await self.write_messages()
        read_task.cancel()

        await self.disconnect()

async def main():
    server_address = os.getenv("HOST", '127.0.0.1')
    server_port = os.getenv("PORT", 8888)
    client = ChatClient(server_address, server_port)
    await client.run()

asyncio.run(main())
