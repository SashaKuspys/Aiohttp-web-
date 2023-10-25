import asyncio
import logging
import subprocess
import websockets
import names
import aiofile
# from aiopath import AsyncPath
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    log_file = "chat_log.txt"  # Шлях до файлу для логування

    async def write_to_log(self, log_message: str):
        async with aiofile.async_open(self.log_file, mode='a') as file:
            await file.write(log_message + '\n')

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == "exchange":
                # Викликаємо код з файлу main.py
                exchange = subprocess.run(["python", "main.py", "1"], stdout=subprocess.PIPE, text=True)
                log_message = exchange.stdout
                await self.send_to_clients(log_message)  # Надсилаємо результат до клієнтів
                await self.write_to_log(log_message)  # Записуємо результат до лог-файлу
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await server.write_to_log("Server started")  # Додаємо лог про запуск сервера
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())