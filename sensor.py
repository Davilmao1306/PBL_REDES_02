from __future__ import annotations

import os
import random
import time
import requests
from common import build_id, env_int, log, split_csv

# Configurações do Sensor injetadas por variáveis de ambiente
SENSOR_ID = os.getenv("SENSOR_ID", build_id("sensor"))
SECTOR_ID = env_int("SECTOR_ID", 1)
BROKERS = split_csv(os.getenv("BROKERS"))
INTERVAL_MIN = env_int("INTERVAL_MIN", 3)
INTERVAL_MAX = env_int("INTERVAL_MAX", 7)

def choose_broker() -> str | None:
    """
    Varre a lista de Brokers conhecidos e escolhe o primeiro que responder.
    Garante que o sensor continue enviando dados mesmo se um broker cair.
    """
    candidates = BROKERS[:]
    random.shuffle(candidates)
    for broker in candidates:
        try:
            # Testa a saúde do broker com um GET rápido
            response = requests.get(f"{broker}/heartbeat", timeout=1.5)
            response.raise_for_status()
            return broker
        except requests.RequestException:
            continue
    return None

def main() -> None:
    if not BROKERS:
        raise SystemExit("Configure BROKERS com uma lista CSV de URLs ex: http://172.16.103.6:8001")

    log(SENSOR_ID, f"Iniciado no setor {SECTOR_ID}; monitorando brokers={BROKERS}")
    
    while True:
        broker = choose_broker()
        if broker is None:
            log(SENSOR_ID, "Nenhum broker ativo encontrado na rede local. Aguardando...")
            time.sleep(2)
            continue

        # Simulação de telemetria anômala (Incêndio, invasão, etc.)
        severity = random.randint(1, 5)
        payload = {
            "sector_id": SECTOR_ID,
            "severity": severity,
            "sensor_id": SENSOR_ID,
            "description": f"Alerta de telemetria critica no setor {SECTOR_ID}, severidade {severity}",
        }
        
        try:
            # PROTOCOLO HTTP POST: Injeta o problema na fila global do Broker escolhido
            response = requests.post(f"{broker}/occurrences", json=payload, timeout=2)
            response.raise_for_status()
            data = response.json()
            log(SENSOR_ID, f"Ocorrencia {data['occurrence_id']} gerada com sucesso no broker {broker}")
        except requests.RequestException:
            log(SENSOR_ID, f"Falha de rede ao reportar para {broker}. Tentando reenviar no proximo ciclo.")

        # Aguarda um tempo aleatório antes de ler os sensores novamente
        time.sleep(random.randint(INTERVAL_MIN, INTERVAL_MAX))

if __name__ == "__main__":
    main()
