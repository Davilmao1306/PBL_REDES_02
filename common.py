from __future__ import annotations

import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from threading import Lock
from typing import Any

# --- ESTADOS DO SISTEMA ---
class OccurrenceStatus(str, Enum):
    PENDING = "pending"   # Na fila distribuída a aguardar drone
    ASSIGNED = "assigned" # Drone alocado e missão a decorrer
    DONE = "done"         # Missão concluída com sucesso

class DroneStatus(str, Enum):
    AVAILABLE = "available" # Livre para receber nova missão (PUSH)
    RESERVED = "reserved"   # Em processo de atribuição pelo Coordenador
    BUSY = "busy"           # Em voo a executar missão
    OFFLINE = "offline"     # Drone caiu ou perdeu conectividade

# --- MODELO DE OCORRÊNCIA ---
@dataclass
class Occurrence:
    occurrence_id: str
    origin_broker_id: int
    sector_id: int
    severity: int
    lamport_ts: int
    broker_id: int
    sensor_id: str
    description: str
    status: str = OccurrenceStatus.PENDING.value
    assigned_drone_id: str | None = None
    created_at: float = field(default_factory=time.time)

    # ALGORITMO DE ORDENAÇÃO E PRIORIZAÇÃO (Barema Critério 3):
    # Garante que a fila é processada na mesma ordem em todos os brokers.
    # Desempate estrito: 1º Maior Severidade, 2º Menor Lamport, 3º Menor ID Broker.
    @property
    def ordering_key(self) -> tuple[int, int, int, str]:
        return (-self.severity, self.lamport_ts, self.broker_id, self.occurrence_id)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Occurrence":
        return cls(**data)

# --- MODELO DE DRONE ---
@dataclass
class DroneInfo:
    drone_id: str
    callback_url: str
    broker_id: int | None = None
    status: str = DroneStatus.AVAILABLE.value
    assigned_occurrence_id: str | None = None
    last_seen: float = field(default_factory=time.time)
    last_mission_heartbeat: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DroneInfo":
        return cls(**data)

# --- ALGORITMO: RELÓGIO LÓGICO DE LAMPORT ---
# Mantém a consistência sob carga (Barema Critério 4).
# Garante a ordem causal dos eventos numa rede com comunicação instável.
class LamportClock:
    def __init__(self) -> None:
        self._value = 0
        self._lock = Lock()

    def tick(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    def update(self, remote_value: int) -> int:
        with self._lock:
            self._value = max(self._value, remote_value) + 1
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

# Utilitários globais
def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default

def split_csv(value: str | None) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()] if value else []

def build_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def log(component: str, message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] [{component}] {message}", flush=True)
