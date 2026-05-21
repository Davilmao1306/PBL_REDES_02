# 🚁 Infraestrutura Distribuída para Coordenação de Drones Marítimos

**Problema 2 — Desbloqueio do Estreito de Ormuz (PBL de Redes de Computadores)**

Este repositório contém a solução para o problema de coordenação distribuída e descentralizada de uma frota partilhada de drones autónomos de monitorização marítima, aplicados na escolta de comboios civis e reconhecimento de rotas seguras no Estreito de Ormuz.

---

## 🌊 Contexto e Desafio Operacional

Face à instabilidade geopolítica no Estreito de Ormuz e aos seus impactos na economia e abastecimento logístico, a área operacional foi dividida em setores marítimos autónomos. Cada setor possui os seus próprios recursos (radares costeiros, boias inteligentes, sensores navais). No entanto, a frota de drones é um **recurso partilhado** por todos os setores.

O sistema opera sob condições severas: **comunicação altamente instável**, grande volume de eventos simultâneos e destruição de equipamentos. A solução elimina qualquer ponto único de falha e resolve conflitos de concorrência na alocação de recursos através de algoritmos distribuídos.

---

## 🏗️ Estilo Arquitetural

O sistema adota o estilo arquitetural **P2P (Peer-to-Peer) Híbrido baseado em Brokers Distribuídos**. Não existe um servidor centralizador.
* **📡 Sensores (IoT):** Dispositivos autónomos que monitorizam o oceano e injetam requisições de anomalias (ocorrências com severidade de 1 a 5) nos brokers.
* **🧠 Brokers de Setor:** Nós da rede distribuída que gerem as filas de cada setor, replicam estados entre si e elegem um coordenador temporário.
* **🚁 Drones Autónomos:** Unidades de execução que respondem a comandos, realizam as missões simuladas e reportam a sua disponibilidade.

---

## 🔌 Paradigma de Comunicação: Arquitetura PUSH

Uma das principais decisões de projeto desta infraestrutura foi a escolha de uma **Arquitetura Baseada em PUSH** para o fluxo de mensagens, em detrimento de uma abordagem baseada em PULL (Polling).



### Como funciona o Modelo PUSH no sistema:
1. **Injeção de Alertas (Sensor ➡️ Broker):** Quando um sensor deteta uma anomalia, ele **empurra (Push)** os dados imediatamente para o endpoint `/occurrences` de um broker ativo via HTTP POST.
2. **Despacho de Missões (Coordenador ➡️ Drone):** Os drones expõem um servidor HTTP interno (FastAPI). Quando o Broker Coordenador decide alocar uma missão, ele faz um **Push** ativando o endpoint `/mission` do drone escolhido.
3. **Sinal de Vida em Voo (Drone ➡️ Brokers):** Durante a execução da missão, o drone **empurra (Push)** atualizações periódicas a cada 2 segundos para manter o seu registo de atividade (`last_seen`) atualizado nos brokers.

### Justificação Técnica: Porquê PUSH e não PULL?
Num modelo **PULL**, os drones teriam de efetuar requisições contínuas (*polling*) aos brokers perguntando: *"Há algum trabalho para mim?"*. Isto violaria as restrições do problema pelos seguintes motivos:
* **Desperdício de Banda numa Rede Instável:** Manter 8 ou mais drones a inundar a rede com requisições HTTP em loops infinitos consumiria largura de banda preciosa num canal de comunicação já debilitado e instável como o do estreito.
* **Latência de Atendimento:** No modelo Pull, se um drone demorasse 3 segundos entre verificações, uma ocorrência Crítica (Severidade 5) poderia ficar à espera do próximo ciclo. Com o modelo **Push**, o broker atômico delega a missão **no milissegundo exato** em que a ocorrência entra na fila e um drone fica livre, garantindo tempo real de resposta.

---

## ⚙️ Concorrência e Algoritmos Distribuídos

Para assegurar a consistência dos dados e cumprir rigorosamente as restrições operacionais, foram aplicados os seguintes algoritmos:

### 1. Ordenação Causal com Relógio Lógico de Lamport
Para mitigar os atrasos e falhas de rede, cada evento possui um carimbo de tempo lógico (`LamportClock`). A fila distribuída ordena as prioridades com base numa chave de ordenação estrita (`ordering_key`):
$$\text{Prioridade} = \text{Maior Severidade} \rightarrow \text{Menor Timestamp de Lamport} \rightarrow \text{Menor ID do Broker}$$
Isto garante que todos os brokers reconstruam a fila **exatamente na mesma ordem**, independentemente de quando as mensagens chegam fisicamente.

### 2. Exclusão Mútua Distribuída (Eleição de Líder)
Para garantir que **um mesmo drone nunca seja reservado para duas missões simultâneas** e que **não haja duplicidade de cobertura** na mesma área, o sistema elege deterministicamente um **Coordenador Temporário**. 
* O coordenador ativo será sempre o broker online que possuir o **menor ID numérico** (ex: `broker-1`).
* Apenas este líder tem autorização para executar o loop de despacho (`dispatch_once()`), atuando como o trinco (*lock*) centralizado de exclusão mútua da rede distributed.

### 3. Tolerância a Falhas e Replaneamento Automático
* **Queda de Broker:** Os brokers vigiam-se mutonamente via *Heartbeats* a cada 2s. Se o líder cair, o próximo menor ID ativo assume as rédeas do despacho imediatamente.
* **Queda de Drone em Missão:** Graças ao fluxo contínuo de **Push Heartbeats** do drone, se ele for abatido ou perder o sinal, o Coordenador deteta a ausência de sinal em mais de 6 segundos, altera o estado do drone para `OFFLINE` e faz o **replaneamento**, devolvendo a ocorrência para a fila como `PENDING` para que outro drone a assuma.

---

## 🚀 Como Executar o Projeto

O ambiente é totalmente isolado e emulado através de contentores **Docker**.

### Pré-requisitos
* Git instalado.
* Docker e Docker Compose instalados.

### 1. Clonar ou Atualizar o Código
Para descarregar o repositório original:
```bash
git clone [https://github.com/davilmao1306/pbl_redes_02.git](https://github.com/davilmao1306/pbl_redes_02.git)
cd pbl_redes_02
