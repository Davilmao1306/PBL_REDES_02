import os
import random
import time
import requests
from common import build_id, env_int, log, split_csv

DRONE_ID = os.getenv("DRONE_ID", build_id("drone"))
BROKERS = split_csv(os.getenv("BROKERS"))
MISSION_MIN_SECONDS = env_int("MISSION_MIN_SECONDS", 4)
MISSION_MAX_SECONDS = env_int("MISSION_MAX_SECONDS", 9)

def get_brokers() -> list[str]:
    candidates = BROKERS[:]
    random.shuffle(candidates)
    return candidates

def main():
    if not BROKERS:
        raise SystemExit("Configure BROKERS com uma lista CSV de URLs")
        
    log(DRONE_ID, f"Iniciado em modo PULL (Resiliente); brokers={BROKERS}")
    
    while True:
        assigned_occurrence = None
        coordinator_broker = None
        
        # 1. PERGUNTA AOS BROKERS SE EXISTE MISSÃO PARA COLETAR
        for broker in get_brokers():
            try:
                # Sinaliza que está online (Heartbeat regular)
                requests.post(f"{broker}/drones/register", json={"drone_id": DRONE_ID, "callback_url": "modo-pull"}, timeout=1)
                
                # Faz o Pull da tarefa
                response = requests.post(f"{broker}/missions/pull", json={"drone_id": DRONE_ID}, timeout=1.5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "assigned":
                        assigned_occurrence = data["occurrence"]
                        coordinator_broker = broker
                        break
            except requests.RequestException:
                continue
        
        # 2. SE COLETOU UMA MISSÃO, EXECUTA O VOO
        if assigned_occurrence:
            occ_id = assigned_occurrence["occurrence_id"]
            duration = random.randint(MISSION_MIN_SECONDS, MISSION_MAX_SECONDS)
            log(DRONE_ID, f"Missao REQUISITADA: {occ_id}. Executando voo por {duration}s...")
            
            # Durante a execução, continua enviando heartbeats para o broker saber que não caiu
            for _ in range(duration):
                time.sleep(1)
                try:
                    requests.post(f"{coordinator_broker}/drones/register", json={"drone_id": DRONE_ID, "callback_url": "modo-pull"}, timeout=1)
                except:
                    pass
            
            # 3. CONCLUI A MISSÃO
            payload = {"occurrence_id": occ_id, "drone_id": DRONE_ID}
            for broker in get_brokers():
                try:
                    requests.post(f"{broker}/missions/done", json=payload, timeout=2)
                    log(DRONE_ID, f"Missao {occ_id} encerrada e reportada com sucesso!")
                    break
                except requests.RequestException:
                    continue
        else:
            # Fila vazia, aguarda 2 segundos e tenta puxar novamente
            time.sleep(2)

if __name__ == "__main__":
    main()
