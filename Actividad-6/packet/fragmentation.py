from packet.packet import HEADER_SIZE, Packet


def fragment_IP_packet(IP_packet: bytes, MTU: int) -> list[bytes]:
    """Divide un paquete IP (o un fragmento) en fragmentos que caben en un enlace con el MTU dado.
    Params:
        IP_packet: paquete IP completo en bytes, con headers incluidos
        MTU: cantidad máxima de bytes (header + mensaje) que pasan por el enlace
    Returns:
        lista de fragmentos en bytes, ordenados por offset. Si el paquete cabe en el MTU, retorna [IP_packet]
    """
    if len(IP_packet) <= MTU:
        return [IP_packet]
    packet = Packet.from_bytes(IP_packet)
    chunk_size = MTU - HEADER_SIZE
    fragments = []
    for start in range(0, packet.SIZE, chunk_size):
        chunk = packet.msg[start: start + chunk_size]
        is_last = start + chunk_size >= packet.SIZE
        # el offset es relativo al datagrama original, por eso se suma el offset del paquete recibido.
        # solo el último trozo hereda el FLAG: si se re-fragmenta un fragmento intermedio, vienen más después
        fragment = Packet(packet.IP, packet.PORT, chunk, packet.TTL, packet.ID,
                          packet.OFFSET + start, packet.FLAG if is_last else 1)
        fragments.append(fragment.to_bytes())
    return fragments


def reassemble_IP_packet(fragment_list: list[bytes]) -> bytes | None:
    """Reconstruye el paquete IP original a partir de sus fragmentos, que pueden venir desordenados.
    Params:
        fragment_list: fragmentos en bytes (con headers) de un mismo paquete, es decir, con el mismo ID
    Returns:
        el paquete IP original en bytes, o None si la lista está incompleta
    """
    fragments = sorted((Packet.from_bytes(fragment) for fragment in fragment_list), key=lambda f: f.OFFSET)
    next_offset = 0
    flag = 1
    for fragment in fragments:
        if fragment.OFFSET != next_offset:  # falta el fragmento que empieza en next_offset
            return None
        next_offset += fragment.SIZE
        flag = fragment.FLAG
    if flag != 0:  # falta el fragmento final
        return None
    first = fragments[0]
    msg = b"".join(fragment.msg for fragment in fragments)
    return Packet(first.IP, first.PORT, msg, first.TTL, first.ID).to_bytes()
