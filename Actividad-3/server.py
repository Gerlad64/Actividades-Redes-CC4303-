import socket

from config import *

if __name__ == '__main__':

    print("-------SERVER-----")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SERVER_ADDRESS)
    while True:
        try:
            message, address = sock.recvfrom(4000)
            print(message)
            if message.find(b'EOF') != -1:
                sock.sendto(b'OK', address)
        except KeyboardInterrupt:
            sock.close()
            break
    print("Programa Finalizado")