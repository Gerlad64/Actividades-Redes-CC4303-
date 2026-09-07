import socket

from config import *
from dns_parser import DNS, decompress_name, ip_to_str, name_to_str

template_dns = DNS.from_bytes(
    0x00_00_00_00_00_01_00_00_00_00_00_00.to_bytes(12)+
    0x00_00_01_00_01.to_bytes(5) # sin dominio (\x00), qtype "A" y qclass 1
)
count = 0
def resolver(dns_bytes: bytes, ip_addr: str) -> DNS | None:
    global count
    LOGGER.debug("\033[36mrecursive call\033[0m %s", count)
    count += 1
    # Parte 4.a
    # Envía un mensaje al servidor dns y parsea su respuesta
    response_dns = DNS.from_socket(dns_bytes, ip=ip_addr, port=53) # envía directamente la query
    # Parte 4.b
     
    # Itera sobre todas las respuestas 
    # hasta encontrar una con un registro A
    # Si lo encuentra retorna la respuesta dns
    for i, answer in enumerate(response_dns.answers):
        LOGGER.debug("\033[36m(for: 1): answer\033[0m %s", i)
        if answer.rtype_is("A"):
            count = 0
            LOGGER.debug("\033[36m(if: 1) Respuesta A encontrada:\033[0m %s", ip_to_str(answer.rddta[:4]))
            return response_dns
    
    LOGGER.debug("\033[36mNo se encontraron Respuestas de tipo A\033[0m")
    LOGGER.debug("\033[36mSe procede a buscar registros Authority de tipo NS\033[0m")
     
    # Parte 4.c cuando no se cumplen las condiciones solicitadas
    # Se queda con el primer registro de tipo NS que encuentra
    authority = next((auth for auth in response_dns.authority_records if auth.rtype_is("NS")), None)
    if authority is None: # Si no hay, nada más que hacer
        count = 0
        LOGGER.debug("\033[36m(if: 2) No hay sección Authority de tipo NS\033[0m")
        return None

    LOGGER.debug("\033[36mSe encontró un registro Authority\033[0m")
    LOGGER.debug("\033[36mBuscando IPs en registros Additional\033[0m")
    
    # Parte 4.c.i
    # Dado que hay un NS, se busca su IP en additional
    # Si la encuentra, debe resolver la query original con esa IP
    for i, addt in enumerate(response_dns.additional_records):
        LOGGER.debug("\033[36m(for: 2): additional record\033[0m %s", i)
        if addt.rtype_is("A"):
            next_ip = socket.inet_ntoa(addt.rddta[:4])
            LOGGER.debug("\033[36m(if: 2) Respuesta A encontrada\033[0m")
            LOGGER.debug("\033[36mConsultando\033[0m '%s' \033[36ma\033[0m '%s' \033[36mcon dirección IP\033[0m '%s'",
    			name_to_str(dns_bytes[12:]),
    			name_to_str(authority.rddta),
    			ip_to_str(addt.rddta[:4])
            )
            # Ahora resuelve usando la IP encontrada
            return resolver(dns_bytes, next_ip)
            
    LOGGER.debug("\033[36mNo se encotraron IPs en los registros Additional\033[0m")
    LOGGER.debug("\033[36mSe procede a resolver el registro Authority\033[0m")
    # Parte 4.c.ii
    # Dado que no resolvió 
    ns_name = decompress_name(authority.rddta[:authority.rdlength], response_dns.to_bytes())
    # Crea consulta a partir de ns_name
    resolved_dns = template_dns.copy()
    assert resolved_dns.question is not None
    resolved_dns.question.qname = ns_name # esto funciona con bytes y str
    
    LOGGER.debug("\033[36mConsultando\033[36m '%s' \033[36ma\033[0m '.' \033[36mcon dirección IP\033[0m '198.41.0.4'", resolved_dns.question._to_str())
    resolved_dns = resolver(resolved_dns.to_bytes(), '198.41.0.4')
    if resolved_dns is None or resolved_dns.answers:
        count = 0
        return None
        
    next_ip = socket.inet_ntoa(resolved_dns.answers[0].rddta[:4])
    return resolver(dns_bytes, next_ip)
    
    
    
    

if __name__ == "__main__":
    print(BANNER)
    
    while True:
        LOGGER.info("\033[32mCreating udp socket\033[0m")
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(SERVER_ADDRESS)
        message, address = udp_socket.recvfrom(SERVER_BUFFER_SIZE)
        LOGGER.info("\033[32mReceived a message\033[0m from: %s", f"{address[0]}:{address[1]}")
        dns = DNS.from_bytes(message)
        
        LOGGER.debug("\033[36mReceived: \033[0m  %s", message.hex())
        LOGGER.debug("\033[36mParsed dns\033[0m: %s\n", dns.to_bytes().hex())
        LOGGER.info("\033[32mResolving\033[0m")
        
        assert dns.question is not None
        LOGGER.debug("\033[36mConsultando '%s' a '.' con dirección IP '198.41.0.4'\033[0m", name_to_str(dns.question.qname))
        dns = resolver(message, "198.41.0.4")
        if dns is None:
            LOGGER.info("\x1b[31mCould not resolve\x1b[0m")
            udp_socket.close()
        else:
            LOGGER.info("\033[32mResolved dns\033[0m:\n %s\n", dns.to_bytes())
            udp_socket.sendto(dns.to_bytes(), address)
            udp_socket.close()
