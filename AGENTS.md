# AGENTS.md

## Context
Repository for the activities of the "Redes" (Networking) course. Each activity (`Actividad-N/`) is a simplified implementation of an Internet protocol, driven by a use case (e.g., an HTTP proxy with the minimum set of required headers).

**Current activity: 6** (update when starting each activity)

Each activity may include an optional `CONTEXT.md` that comes before `ENUNCIADO.md` and holds background and instructions important for the activity. Before writing code, read `CONTEXT.md` if it exists, then `ENUNCIADO.md`.

These are simplified versions: write the minimum code needed to pass the tests defined in the activity statement. Do not add robustness or features that were not requested.

## Boundaries
- Work only inside `Actividad-N/`. Unless you're told to, do not read or modify other activities, especially delivered ones.
- `CONTEXT.md` is read-only.
- `ENUNCIADO.md` is read-only.

## Deliverables
1. **Code** in `Actividad-N/`: must include everything needed to run.
2. **Report** at `Actividad-N/INFORME.md`, written in Spanish (see Report section).

## Stack
- Python 3.13 or newer.
- Standard library: `socket`, `dataclasses`, `ctypes` (for byte handling), plus whatever the statement allows.
- Additional dependencies only if the statement requires them or the user approves them after the agent proposes them.

## Commands
Run from the repository root. The code must pass both checks:
```bash
ty check Actividad-N/
ruff check Actividad-N/
```
To explain a rule that appears in the output:
```bash
ty explain rule <RULE>
ruff rule <RULE>
```

## Style conventions
- Code (identifiers, file names) in English.
- Docstrings and `INFORME.md` in Spanish.
- Structures that parse or build bytes follow the pattern below.

### Pattern for protocol bytes
```python
from __future__ import annotations

import ctypes


class Question(ctypes.BigEndianStructure):
    """Campo `question` de un mensaje DNS. `qname` tiene largo variable, por eso no está en `_fields_`."""

    qtype: int
    qclass: int
    _fields_ = [
        ("qtype", ctypes.c_uint16),
        ("qclass", ctypes.c_uint16),
    ]
    _pack_ = 1

    def __init__(self, qname: bytes = b"\x00", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.qname = qname

    def __bytes__(self) -> bytes:
        return self.qname + bytes(memoryview(self))

    def to_bytes(self) -> bytes:
        return bytes(self)

    @classmethod
    def from_bytes(cls, data: bytes, offset: int = 0) -> Question:
        ...
```
- Inherit from `ctypes.BigEndianStructure` and declare fixed-length fields in `_fields_`.
- Implement `to_bytes(self)` and `from_bytes(cls, ...)`.
- Optionally override `__init__` or add attributes that are not part of the `ctypes` byte layout.

## Architecture and design decisions
- If the statement does not specify a structure or mechanism (e.g., the socket type for HTTP), pick a reasonable option, keep it consistent across the code, and justify it in the report using course material (not included in this repository).
- If the statement seems to contain an error, first verify your own reading. If the problem persists, report it to the user before implementing an alternative.

## Report (`INFORME.md`)
Sections, in this order. Titles and content are in Spanish:
1. **Documentación y diseño:** which file holds each part and where the entry point is.
2. **Clases y estructuras:** code of the main class. For each attribute, explain why that type was chosen, not only what it is.
3. **Flujo:** description of how it works, with a diagram if the statement asks for one.
4. **Dependencias y entorno:** tested Python versions and modules used.
5. **Configuración y ejecución:** configuration files and exact commands.
6. **Pruebas:** cases tested and how to reproduce them.
7. **Uso de IA:** leave `[completar]` so the person can state which parts were generated with AI.

Justify design decisions with short paragraphs and brief code snippets.

## Git
- Work directly on `main`; do not create branches.
- Conventional Commits: `<type>: <short description>`, where `<type>` is `feat`, `fix`, `docs`, `refactor`, `test`, or `chore`.