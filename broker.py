from __future__ import annotations

import os
import threading
import time
from contextlib import asynccontextmanager
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Importações de tipos utilitários comuns do projeto
from common import DroneInfo, DroneStatus, LamportClock, Occurrence, OccurrenceStatus, env_int, log, split_csv
from dashboard import DASHBOARD_HTML

# --- CONFIGURAÇÕES DO AMBIENTE ---
BROKER_ID = env_int("BROKER_ID", 1)
PORT = env_int("PORT", 8000)
BROKER_URL = os.getenv("BROKER_URL", f"http://broker-{BROKER_ID}:{PORT}")
PEERS = split_csv(os.getenv("PEERS"))                  # Lista de Brokers vizinhos na malha P2P
HEARTBEAT_INTERVAL = env_int("HEARTBEAT_INTERVAL", 2)  # Frequência de teste entre Brokers (segundos)
HEARTBEAT_TIMEOUT = env_int("HEARTBEAT_TIMEOUT", 6)   # Limite para considerar que um Broker caiu
DISPATCH_INTERVAL = env_int("DISPATCH_INTERVAL", 1)   # Frequência de monitoramento de drones
DISPATCH_START_DELAY = env_int("DISPATCH_START_DELAY", 5) # Delay de aquecimento inicial do servidor
MAX_EVENTS = env_int("MAX_EVENTS", 80)                 # Limite de logs mantidos na memória para o painel

# --- ESTADO INTERNO DO BROKER (MEMÓRIA COMPARTILHADA) ---
clock = LamportClock()                             # Relógio lógico de Lamport para ordenação de eventos
state_lock = threading.RLock()                     # Lock Reentrante para evitar condições de corrida (Thread-Safety)
occurrences: dict[str, Occurrence] = {}            # Banco de dados na memória para as Ocorrências/Missões
drones: dict[str, DroneInfo] = {}                  # Registro de estado atual de todos os Drones conhecidos
peer_status: dict[int, dict[str, Any]] = {}        # Monitoramento de atividade de Brokers vizinhos
known_brokers: dict[int, str] = {BROKER_ID: BROKER_URL} # Catálogo de IPs/URLs de nós do cluster
events: list[dict[str, Any]] = []                  # Histórico de eventos consumido pelo Dashboard
stop_event = threading.Event()                     # Flag para encerrar threads graciosamente no desligamento
started_at = time.time()                           # Timestamp de inicialização do nó


# --- MODELOS DE ENTRADA DE DADOS (PYDANTIC) ---
class OccurrenceIn(BaseModel):
    sector_id: int
    severity: int
    sensor_id: str
    description: str

class DroneRegistration(BaseModel):
    drone_id: str
    callback_url: str

class PeerState(BaseModel):
    broker_id: int
    broker_url: str
    lamport_ts: int
    occurrences: list[dict[str, Any]]
    drones: list[dict[str, Any]]

class MissionDone(BaseModel):
    occurrence_id: str
    drone_id: str

class MissionPull(BaseModel):
    drone_id: str


# --- FUNÇÕES UTILITÁRIAS E DE INFRAESTRUTURA ---

def broker_log(message: str) -> None:
    """Registra uma mensagem no terminal local e adiciona à fila de visualização do dashboard."""
    component = f"broker-{BROKER_ID}"
    log(component, message)
    with state_lock:
        events.append({"ts": time.time(), "component": component, "message": message})
        del events[:-MAX_EVENTS] # Trunca a lista mantendo apenas os eventos mais recentes


def peer_id_from_url(url: str) -> int | None:
    """Extrai o número ID numérico de um broker através do padrão de URL (ex: broker-2 -> 2)."""
    name = url.rstrip("/").split("//")[-1].split(":")[0]
    if name.startswith("broker-"):
        try:
            return int(name.split("-", 1)[1])
        except ValueError:
            return None
    return None


def active_broker_ids() -> list[int]:
    """Retorna uma lista contendo os IDs de todos os Brokers que estão vivos na rede no momento."""
    now = time.time()
    ids = [BROKER_ID] # Eu mesmo sempre inicio a lista como ativo
    with state_lock:
        for peer_id, status in peer_status.items():
            # Critério de atividade: Marcado como ativo e tempo do último sinal menor que o timeout
            if status.get("alive") and now - status.get("last_seen", 0) <= HEARTBEAT_TIMEOUT:
                ids.append(peer_id)
    return sorted(set(ids))


def coordinator_id() -> int:
    """Algoritmo do Ditador/Bully Simplificado: O menor ID ativo é eleito o Coordenador (Líder)."""
    return min(active_broker_ids())


# --- ALGORITMOS DE CONSISTÊNCIA EVENTUAL (MÉTODO CRÍTICO) ---

def merge_occurrence(data: dict[str, Any]) -> None:
    """Aplica as regras de Lamport para sincronizar atualizações de ocorrências enviadas por peers."""
    incoming = Occurrence.from_dict(data)
    clock.update(incoming.lamport_ts) # Sincroniza o relógio lógico local
    with state_lock:
        current = occurrences.get(incoming.occurrence_id)
        # Sorteia/Mescla: Se o dado for novo ou tiver timestamp lógico maior/igual, sobrescreve o atual
        if current is None or incoming.lamport_ts >= current.lamport_ts:
            occurrences[incoming.occurrence_id] = incoming


def merge_drone(data: dict[str, Any]) -> None:
    """Mescla o estado de drones recebidos via replicação usando abordagem do último carimbo de tempo."""
    incoming = DroneInfo.from_dict(data)
    with state_lock:
        current = drones.get(incoming.drone_id)
        if current is None or incoming.last_seen >= current.last_seen:
            drones[incoming.drone_id] = incoming


def snapshot_state() -> dict[str, Any]:
    """Cria uma foto serializável do estado local para ser transmitida para os outros nós da rede."""
    with state_lock:
        return {
            "broker_id": BROKER_ID,
            "broker_url": BROKER_URL,
            "lamport_ts": clock.tick(),
            "occurrences": [item.to_dict() for item in occurrences.values()],
            "drones": [item.to_dict() for item in drones.values()],
        }


def replicate_state() -> None:
    """Dispara uma cópia do estado local para todos os Brokers cadastrados na lista de vizinhos."""
    payload = snapshot_state()
    for peer in PEERS:
        try:
            requests.post(f"{peer}/peer/state", json=payload, timeout=1.5)
        except requests.RequestException:
            continue


# --- DETECÇÃO DE FALHAS (HEARTBEATS E TIMEOUTS) ---

def mark_peer_alive(peer_id: int, peer_url: str) -> None:
    """Registra ou atualiza um Broker vizinho como ativo e saudável."""
    with state_lock:
        known_brokers[peer_id] = peer_url
        previous = peer_status.get(peer_id, {})
        if not previous.get("alive"):
            broker_log(f"heartbeat: broker {peer_id} ativo em {peer_url}")
        peer_status[peer_id] = {"alive": True, "last_seen": time.time(), "url": peer_url}


def mark_peer_down(peer_id: int) -> None:
    """Modifica o estado de um Broker vizinho para inativo devido à ausência de respostas."""
    with state_lock:
        previous = peer_status.get(peer_id, {})
        if previous.get("alive", True):
            broker_log(f"falha detectada: broker {peer_id} parou de responder")
        peer_status[peer_id] = {**previous, "alive": False, "last_seen": previous.get("last_seen", 0)}


def heartbeat_loop() -> None:
    """Thread ativa contínua focada em monitorar a saúde dos outros Brokers e espalhar dados."""
    for peer in PEERS:
        peer_id = peer_id_from_url(peer)
        if peer_id is not None:
            with state_lock:
                peer_status.setdefault(peer_id, {"alive": False, "last_seen": 0, "url": peer})
                known_brokers[peer_id] = peer

    while not stop_event.is_set():
        for peer in PEERS:
            try:
                response = requests.get(f"{peer}/heartbeat", timeout=1.5)
                response.raise_for_status()
                data = response.json()
                mark_peer_alive(int(data["broker_id"]), data["broker_url"])
            except requests.RequestException:
                peer_id = peer_id_from_url(peer)
                if peer_id is not None:
                    last_seen = peer_status.get(peer_id, {}).get("last_seen", 0)
                    if time.time() - last_seen > HEARTBEAT_TIMEOUT:
                        mark_peer_down(peer_id)
        replicate_state()
        time.sleep(HEARTBEAT_INTERVAL)


def check_failed_missions() -> None:
    """Avalia se drones ocupados pararam de reportar atividade. Travado para execução apenas do Líder."""
    # REVISÃO CRÍTICA (CORREÇÃO): Se eu não for o coordenador ativo, eu permaneço em silêncio.
    # Impede que o Broker backup manipule e corrompa a fila global distribuída.
    if coordinator_id() != BROKER_ID:
        return

    now = time.time()
    TIMEOUT_LIMITE = 6.0 

    with state_lock:
        for drone in list(drones.values()):
            # Se o drone está executando uma tarefa, mas não emite sinal de vida há mais de 6 segundos
            if drone.status == DroneStatus.BUSY.value and drone.assigned_occurrence_id:
                if now - drone.last_seen > TIMEOUT_LIMITE:
                    occ_id = drone.assigned_occurrence_id
                    occ = occurrences.get(occ_id)
                    
                    broker_log(f"[ALERTA TOLERÂNCIA A FALHAS] Drone {drone.drone_id} caiu durante a missao {occ_id}!")
                    drone.status = DroneStatus.OFFLINE.value
                    drone.assigned_occurrence_id = None
                    
                    # Recuperação de Falhas: Libera a ocorrência de volta à fila para ser assumida por outro nó
                    if occ and occ.status != OccurrenceStatus.DONE.value:
                        occ.status = OccurrenceStatus.PENDING.value
                        occ.assigned_drone_id = None
                        occ.lamport_ts = clock.tick()
                        broker_log(f"Ocorrencia {occ_id} restaurada com sucesso para a fila de redistribuicao.")


def dispatch_loop() -> None:
    """Thread contínua de gerenciamento de falhas em missões ativas."""
    while not stop_event.is_set():
        try:
            check_failed_missions()
        except Exception as exc:
            broker_log(f"erro no despachante: {exc}")
        time.sleep(DISPATCH_INTERVAL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Gerenciador de ciclo de vida do FastAPI. Dispara as threads de background na subida do app."""
    broker_log(f"iniciado em {BROKER_URL}; peers={PEERS}")
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    threading.Thread(target=dispatch_loop, daemon=True).start()
    yield
    stop_event.set() # Sinaliza a parada das threads ao encerrar o servidor


# Inicialização do Framework FastAPI
app = FastAPI(title=f"Broker {BROKER_ID}", lifespan=lifespan)


# --- ROTAS HTTP ENDPOINTS (API REST) ---

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    """Renderiza a interface visual web do painel de monitoramento."""
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/heartbeat")
def heartbeat() -> dict[str, Any]:
    """Endpoint de checagem interna entre os brokers para atualização de relógio e topologia."""
    return {"broker_id": BROKER_ID, "broker_url": BROKER_URL, "lamport_ts": clock.tick()}


@app.post("/occurrences")
def create_occurrence(data: OccurrenceIn) -> dict[str, Any]:
    """Recebe novos alertas capturados e transmitidos pelos nós Sensores."""
    ts = clock.tick()
    occurrence = Occurrence(
        occurrence_id=f"occ-{BROKER_ID}-{ts}-{int(time.time() * 1000)}",
        origin_broker_id=BROKER_ID,
        sector_id=data.sector_id,
        severity=max(1, min(5, data.severity)), # Garante valor limítrofe entre 1 e 5
        lamport_ts=ts,
        broker_id=BROKER_ID,
        sensor_id=data.sensor_id,
        description=data.description,
    )
    with state_lock:
        occurrences[occurrence.occurrence_id] = occurrence
    broker_log(f"ocorrencia criada {occurrence.occurrence_id}: prioridade={occurrence.severity} ts={ts}")
    replicate_state() # Força a replicação imediata do novo alerta para o cluster
    return occurrence.to_dict()


@app.post("/drones/register")
def register_drone(data: DroneRegistration) -> dict[str, Any]:
    """Cadastra ou atualiza o sinal de presença (heartbeat) emitido de forma contínua pelo drone."""
    with state_lock:
        drone = drones.get(data.drone_id)
        # Se o drone já existia e está executando missão, apenas renova o tempo de vida dele (Keep-Alive)
        if drone:
            drone.callback_url = data.callback_url
            drone.last_seen = time.time()  # Atualização do timestamp crucial para evitar falsos alarmes de queda
            if drone.status in {DroneStatus.RESERVED.value, DroneStatus.BUSY.value}:
                return {"status": drone.status, "broker_id": BROKER_ID}
        
        # Se for um drone novo, inicializa o registro como Disponível (Available)
        drone = DroneInfo(
            drone_id=data.drone_id,
            callback_url=data.callback_url,
            broker_id=BROKER_ID,
            status=DroneStatus.AVAILABLE.value,
        )
        drone.last_seen = time.time()
        drones[data.drone_id] = drone

    broker_log(f"drone registrado/atualizado: {data.drone_id} em modo PULL")
    replicate_state()
    return {"status": "registered", "broker_id": BROKER_ID}


@app.post("/missions/pull")
def pull_mission(data: MissionPull) -> dict[str, Any]:
    """Rota em que o drone requisita trabalho. Contornando firewalls através do modelo de Pull."""
    if time.time() - started_at < DISPATCH_START_DELAY:
        return {"status": "starting_up"}
        
    # PROTEÇÃO CRÍTICA: Bloqueia a liberação de missões se a requisição bater em um Broker de Backup
    if coordinator_id() != BROKER_ID:
        return {"status": "not_coordinator"}

    with state_lock:
        drone = drones.get(data.drone_id)
        if not drone:
            return {"status": "not_registered"}
            
        if drone.status == DroneStatus.BUSY.value:
            return {"status": "already_busy"}

        # Extrai e ordena a lista de pendentes seguindo a regra estruturada: Severidade decrescente e Relógio Crescente
        pending = sorted(
            [item for item in occurrences.values() if item.status == OccurrenceStatus.PENDING.value],
            key=lambda item: item.ordering_key,
        )
        
        if not pending:
            return {"status": "no_mission"}

        # Captura e remove a missão mais prioritária da fila
        occurrence = pending.pop(0)
        occurrence.status = OccurrenceStatus.ASSIGNED.value
        occurrence.assigned_drone_id = drone.drone_id
        occurrence.lamport_ts = clock.tick()
        
        # Atualiza os dados do drone selecionado vinculando-o à tarefa
        drone.status = DroneStatus.BUSY.value
        drone.assigned_occurrence_id = occurrence.occurrence_id
        drone.last_seen = time.time()
        
    broker_log(f"Missao {occurrence.occurrence_id} ENTREGUE via PULL para o drone {drone.drone_id}")
    replicate_state() # Sincroniza o cluster P2P sobre a alocação da missão
    return {"status": "assigned", "occurrence": occurrence.to_dict()}


@app.post("/missions/done")
def mission_done(data: MissionDone) -> dict[str, Any]:
    """Endpoint chamado pelo drone ao finalizar com sucesso o percurso da missão."""
    with state_lock:
        occurrence = occurrences.get(data.occurrence_id)
        drone = drones.get(data.drone_id)
        
        if occurrence is None:
            raise HTTPException(status_code=404, detail="occurrence not found")
            
        # Altera o estado da ocorrência para Concluída (Done)
        occurrence.status = OccurrenceStatus.DONE.value
        occurrence.assigned_drone_id = data.drone_id
        occurrence.lamport_ts = clock.tick()
        
        # Libera o drone associado deixando-o pronto para buscar novas tarefas
        if drone:
            drone.status = DroneStatus.AVAILABLE.value
            drone.assigned_occurrence_id = None
            drone.last_seen = time.time()
            
    broker_log(f"missao concluida com sucesso: {data.occurrence_id} por {data.drone_id}")
    replicate_state()
    return {"status": "done"}


@app.post("/peer/state")
def receive_peer_state(data: PeerState) -> dict[str, Any]:
    """Endpoint de recepção de dados replicados focado em unificar a visão global de todos os nós."""
    mark_peer_alive(data.broker_id, data.broker_url)
    clock.update(data.lamport_ts)
    
    # Processa as atualizações mesclando as filas de ocorrências e listas de drones
    for occurrence in data.occurrences:
        merge_occurrence(occurrence)
    for drone in data.drones:
        merge_drone(drone)
        
    return {"status": "merged", "broker_id": BROKER_ID, "coordinator_id": coordinator_id()}


@app.get("/state")
def state() -> dict[str, Any]:
    """Exporta o snapshot completo do sistema estruturado em JSON para o Dashboard visual frontend."""
    with state_lock:
        pending_order = sorted(
            [item for item in occurrences.values() if item.status == OccurrenceStatus.PENDING.value],
            key=lambda item: item.ordering_key,
        )
        return {
            "broker_id": BROKER_ID,
            "broker_url": BROKER_URL,
            "lamport_ts": clock.value,
            "coordinator_id": coordinator_id(),
            "active_brokers": active_broker_ids(),
            "known_brokers": dict(known_brokers),
            "peer_status": {peer_id: dict(status) for peer_id, status in peer_status.items()},
            "pending_queue": [item.to_dict() for item in pending_order],
            "occurrences": [item.to_dict() for item in occurrences.values()],
            "drones": [item.to_dict() for item in drones.values()],
            "events": list(events),
        }
