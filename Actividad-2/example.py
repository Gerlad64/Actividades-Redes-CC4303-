import binascii
import socket

from dns_parser import *

def send_dns_message(address, port):
    # Encabezado con ID 0 (00 00 en hexadecimal), preguntamos por example.com
    header = "00 00 00 00 00 01 00 00 00 00 00 00 ".replace(" ","")
    data = "07 65 78 61 6D 70 6C 65 03 63 6F 6D 00 00 01 00 01".replace(" ","")
    message = header + data
    # Lo escribimos así para que se entendiera, lo concatenamos para hacer la cadena de hexadecimales
    server_address = (address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # usamos binascii para pasar el mensaje al formato apropiado
        binascii_msg = binascii.unhexlify(message)
        # y lo enviamos
        sock.sendto(binascii_msg, server_address)
        # En data quedará la respuesta a nuestra consulta
        data, _ = sock.recvfrom(4096)
    finally:
        sock.close()
    # Ojo que los datos de la respuesta van en hexadecimal, no en binario
    return binascii.hexlify(data).decode("utf-8")

def my_send_dns_message(address, port):
    print("--------DNS Message-------")
    dns = DNS.from_bytes(
        0x00_00_00_00_00_01_00_00_00_00_00_00.to_bytes(12)+
        0x07_65_78_61_6D_70_6C_65_03_53_6F_6D_00_00_01_00_01.to_bytes(17)
    )
    print("Message_", dns.to_bytes())
    server_address = (address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
            # usamos binascii para pasar el mensaje al formato apropiado
            # y lo enviamos
            sock.sendto(dns.to_bytes(), server_address)
            # En data quedará la respuesta a nuestra consulta
            data, _ = sock.recvfrom(4096)
    finally:
            sock.close()
        # Ojo que los datos de la respuesta van en hexadecimal, no en binario
    print("--------DNS Response-------")
    print(data)
    print("------")
    return DNS.from_bytes(data).to_bytes()
    
def my_send_dns_message2(address, port):
    print("--------DNS Message-------")
    dns = DNS.from_bytes(
        0x00_00_00_00_00_01_00_00_00_00_00_00.to_bytes(12)+
        0x07_65_78_61_6D_70_6C_65_03_53_6F_6D_00_00_01_00_01.to_bytes(17)
    )
    print("Message_", dns.to_bytes())
    server_address = (address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
            # usamos binascii para pasar el mensaje al formato apropiado
            # y lo enviamos
            sock.sendto(dns.to_bytes(), server_address)
            # En data quedará la respuesta a nuestra consulta
            data, _ = sock.recvfrom(4096)
    finally:
            sock.close()
        # Ojo que los datos de la respuesta van en hexadecimal, no en binario
    print("--------DNS Response-------")
    print(data)
    print("------")
    return DNS.from_bytes(data).to_bytes()
if __name__ == '__main__':
    
    print(my_send_dns_message("8.8.8.8", 53))