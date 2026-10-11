from Segment import Segment


class HandshakeErr(Exception):
    """ HandshakeErr hereda de Exception
        Clase para ser lanzada como excepción general en el *three way handshake*

    Attributes:
        message: Mensaje de error
        step: Paso específico del *three way handshake* en el que ocurrió el error,
        por ejemplo, `while processing SYN+ACK`.
        
    """
    def __init__(self, message: str, step: str):
        super().__init__(message)
        self.message = message
        self.step = step

    def __str__(self):
        return f"Handshake Error: {self.message} at handshake step {self.step}"



class SequenceErr(HandshakeErr):
    """Error cuando el número de secuencia no es el esperado"""
    def __init__(
        self,
		expected: int,
		actual: int,
		step: str
    ): 
        super().__init__(
            message = (
                f"Unexpected sequence number: "
                f"expected: {expected}; got: {actual}"
            ),
            step=step
        )

class SegmentFlagsErr(HandshakeErr):
    """Error cuando las flags del segmento no son las esperadas"""
    def __init__(self,
		expected: int | Segment,
		actual: int | Segment,
		step: str,
		at_least=False
    ):
        expected_str = Segment.intflag_to_str(expected) if isinstance(expected, int) else expected.flag_to_str()
        actual_str = Segment.intflag_to_str(actual) if isinstance(actual, int) else actual.flag_to_str()
        at_least_str = " at least" if at_least else ""

        super().__init__(
            message=(
                f"Expected{at_least_str} "
                f"flags: {expected_str}; got: {actual_str}"
            ),
            step=step
        )