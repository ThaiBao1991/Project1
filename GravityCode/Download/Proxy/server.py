import socket
import threading
import select
import time

class ProxyServer:
    def __init__(self, host='127.0.0.1', port=8888, mode='DPI_BYPASS', upstream_proxy=None):
        self.host = host
        self.port = int(port)
        self.mode = mode
        self.upstream_proxy = upstream_proxy # "IP:PORT"
        self.running = False
        self.server_socket = None

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)
        
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    def accept_loop(self):
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
            except:
                break

    def handle_client(self, client_sock):
        try:
            request = client_sock.recv(4096)
            if not request:
                return
            
            headers = request.split(b'\r\n')
            first_line = headers[0].decode('utf-8', errors='ignore')
            method, url, version = first_line.split(' ')

            if method == 'CONNECT':
                host, port = url.split(':')
                port = int(port)

                if self.mode == 'FREE_PROXY' and self.upstream_proxy:
                    # Chuyển tiếp CONNECT request đến Free Proxy
                    proxy_host, proxy_port = self.upstream_proxy.split(':')
                    proxy_port = int(proxy_port)
                    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote_sock.settimeout(5)
                    remote_sock.connect((proxy_host, proxy_port))
                    remote_sock.sendall(request)
                    self.bridge(client_sock, remote_sock)
                else:
                    # Chế độ DPI_BYPASS hoặc DIRECT
                    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # Quan trọng: Tắt Nagle's algorithm để đảm bảo gói tin nhỏ được gửi đi ngay lập tức
                    remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    remote_sock.settimeout(10)
                    remote_sock.connect((host, port))
                    
                    # Trả lời client là kết nối thành công (giả vờ như HTTP CONNECT đã hoàn tất)
                    client_sock.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                    
                    if self.mode == 'DPI_BYPASS':
                        # Chờ đọc ClientHello từ Client (thường là gói tin đầu tiên sau khi CONNECT để thiết lập TLS)
                        client_sock.setblocking(False)
                        ready = select.select([client_sock], [], [], 2.0)
                        if ready[0]:
                            hello_data = client_sock.recv(8192)
                            if hello_data:
                                # DPI Bypass: Cắt nhỏ gói tin Client Hello thành các mảnh nhỏ
                                # Việc này giúp lừa hệ thống quét gói tin của nhà mạng (SNI filtering)
                                try:
                                    # Gửi 5 byte đầu tiên (TLS Record Header) nguyên vẹn để tránh Cloudflare báo lỗi protocol
                                    remote_sock.sendall(hello_data[:5])
                                    time.sleep(0.01)
                                    # Cắt ngang phần SNI ở giữa
                                    mid = len(hello_data) // 2
                                    if mid > 5:
                                        remote_sock.sendall(hello_data[5:mid])
                                        time.sleep(0.01)
                                        remote_sock.sendall(hello_data[mid:])
                                    else:
                                        remote_sock.sendall(hello_data[5:])
                                except:
                                    pass
                    
                    # Bắt đầu cầu nối dữ liệu 2 chiều bình thường
                    self.bridge(client_sock, remote_sock)
            else:
                # Không hỗ trợ giao thức HTTP thuần, vì mục tiêu là bypass HTTPS
                client_sock.close()
        except Exception as e:
            pass
        finally:
            client_sock.close()

    def bridge(self, sock1, sock2):
        sockets = [sock1, sock2]
        while self.running:
            try:
                r, w, e = select.select(sockets, [], [], 1)
                if e:
                    break
                for s in r:
                    data = s.recv(8192)
                    if not data:
                        return
                    if s is sock1:
                        sock2.sendall(data)
                    else:
                        sock1.sendall(data)
            except:
                break
