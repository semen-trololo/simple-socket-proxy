import socket
import threading

# Настройки прокс
local_host = '127.0.0.1'
local_port = 53
remote_host = '192.168.0.1'
remote_port = 53
receive_first = False
protocol = 'UDP'

def hexdump(src, length=16):
    """ Функция вывода хеш дампа данных"""
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    lines = []
    for c in range(0, len(src), length):
        chars = src[c:c+length]
        hex = ' '.join(["%02x" % ord(x) for x in chars])
        printable = ''.join(["%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in chars])
        lines.append("%04x  %-*s  %s\n" % (c, length*3, hex, printable))
    return ''.join(lines)

def receive_from(connection):
    connection.settimeout(60)
    try:
        data = connection.recv(4096)
    except:
        pass
    return data

def receive_from_udp(connection):
    connection.settimeout(5)
    try:
        data, addres = connection.recvfrom(4096)
    except:
        data = ''
        addres = ('', 0)
        return data, addres
    return data, addres

def request_handler(buffer):
    """ Здесть можем написать обработку взодящих данных"""
    return buffer

def response_handler(buffer):
    """ Здесь можем написать обработку изходящих данных """
    return buffer

def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))
    # Если сначало нужно получить ответ от удаленого пользователя.
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        remote_buffer = response_handler(remote_buffer)
        if len(remote_buffer):
            print("[<==] Sending %d bytes to localhost." % len(remote_buffer))
            client_socket.send(remote_buffer)
    while True:
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            print("[==>] Received %d bytes from localhost." % len(local_buffer))
            print(hexdump(local_buffer.decode('utf-8')))
            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            print(hexdump(remote_buffer.decode('utf-8')))
            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost.")
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break
def server_loop_udp(local_host, local_port, remote_host, remote_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server.bind((local_host, local_port))
    except:
        print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
    print("[*] Listening on %s:%d" % (local_host, local_port))
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        local_buffer, local_addr = receive_from_udp(server)
        if len(local_buffer):
            last_addr = local_addr
            print("[==>] Received %d bytes from localhost." % len(local_buffer))
            print(hexdump(local_buffer.decode('utf-8', 'backslashreplace')))
            local_buffer = request_handler(local_buffer)
            remote_socket.sendto(local_buffer, (remote_host, remote_port))
            print("[==>] Sent to remote.")
        remote_buffer, remore_addr = receive_from_udp(remote_socket)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            print(hexdump(remote_buffer.decode('utf-8', 'backslashreplace')))
            remote_buffer = response_handler(remote_buffer)
            if local_addr[0] == '':
                server.sendto(remote_buffer, last_addr)
            else:
                server.sendto(remote_buffer, local_addr)
            print("[<==] Sent to localhost.")

def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host, local_port))
    except:
        print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
    print("[*] Listening on %s:%d" % (local_host, local_port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        print("[==>] Received incoming connection from %s:%d" % (addr[0], addr[1]))
        proxy_thread = threading.Thread(target=proxy_handler, args=(client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()

if protocol == 'UDP' :
    server_loop_udp(local_host, local_port, remote_host, remote_port)
else:
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)
