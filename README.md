# 🚁 Infraestrutura Distribuída para Coordenação de Drones Marítimos

**Problema 2 — Desbloqueio do Estreito de Ormuz (PBL Redes de Computadores)**

Este projeto implementa uma arquitetura de sistemas distribuídos para coordenar uma frota autônoma de drones em um cenário de monitoramento marítimo crítico. O sistema resolve desafios de concorrência, alocação de recursos compartilhados e tolerância a falhas sem depender de um servidor central, empregando algoritmos de coordenação descentralizada.

---

## 🌊 Contexto do Problema

Devido à instabilidade no Estreito de Ormuz, foi necessária a criação de uma força-tarefa para estabilização logística. A área foi dividida em setores marítimos, cada um monitorado por sensores autônomos e gerenciado por **Brokers** descentralizados. Uma frota de **Drones** atua como recurso compartilhado entre todos os setores, atendendo ocorrências como embarcações à deriva ou bloqueios de rotas. 

O desafio central desta solução é **garantir a alocação correta e priorizada de drones em um ambiente de rede instável, sem pontos únicos de falha e sem permitir o envio de dois drones para a mesma missão.**

---

## 🏗️ Arquitetura da Solução

O sistema emprega uma arquitetura **P2P (Peer-to-Peer) Híbrida** (Brokers descentralizados), dividida nos seguintes papéis:

* **📡 Sensores (IoT):** Geradores de dados autônomos. Enviam requisições de anomalias com níveis de severidade (1 a 5) para qualquer Broker ativo.
* **🧠 Brokers (Gerenciadores de Setor):** Mantêm a fila distribuída de requisições. Eles se comunicam constantemente para replicar estado (Snapshot Anti-Entropia) e elegem um Coordenador dinâmico.
* **🚁 Drones (Executores):** Frota compartilhada. Possuem um servidor HTTP interno para receber ordens do broker coordenador, reportando sinais de vida (*heartbeats*) durante os voos.

### 🔌 Protocolo de Comunicação
* Todo o ecossistema utiliza chamadas **HTTP (REST)** sobre o protocolo **TCP**, encapsulando as mensagens no formato **JSON**.
* Padrões de requisições tolerantes a falhas: Uso estrito de `timeouts` para evitar travamento em chamadas perdidas.

---

## ⚙️ Concorrência e Algoritmos Distribuídos

Para atender aos requisitos estritos de concorrência, as seguintes técnicas foram implementadas:

1. **Ordenação de Fila e Lamport Clock:**
   A escolha da próxima ocorrência obedece a um critério de desempate determinístico para evitar colisões:
   * **1º:** Maior Severidade (1 a 5).
   * **2º:** Menor *Relógio Lógico de Lamport* (Garante a ordem causal em nós assíncronos).
   * **3º:** Menor ID do Broker originário.

2. **Exclusão Mútua Distribuída (Eleição de Líder):**
   Não há "servidor chefe". O sistema descobre os pares ativos e define como **Coordenador Temporário** o Broker online com o **menor ID**. Apenas este coordenador tem a permissão de casar drones livres com ocorrências pendentes, garantindo **exclusão mútua** absoluta (zero duplicidade na alocação).

3. **Tolerância a Falhas e Replanejamento:**
   * **Falha de Broker:** Monitorada via *Heartbeat* a cada 2s. Se um broker morre, a rede redistribui suas ocorrências pendentes e, se ele era o coordenador, o próximo ID assume instantaneamente.
   * **Falha de Drone (Abatido/Desconectado):** Durante uma missão, o drone emite sinais de progresso. Se o Coordenador ficar 6 segundos sem ouvir o drone ocupado, ele é declarado **OFFLINE**, e a ocorrência é devolvida para a Fila Distribuída, acionando o envio de um novo drone livre.

---

## 🚀 Como Executar o Projeto

O projeto utiliza **Docker** para garantir o isolamento total dos processos, emulando máquinas físicas distintas em uma mesma rede virtual.

### Pré-requisitos
* Docker e Docker Compose instalados.

### Subindo a Malha Completa
O `docker-compose.yml` está configurado para subir automaticamente **4 Brokers, 4 Sensores e 8 Drones**:

```bash
docker compose up --build
