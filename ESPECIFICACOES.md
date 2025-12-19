# Plano de Implementação: Simulador de Escalonamento Tempo Real (RTS)


**Contexto:**
Você deve agir como um Engenheiro de Software Sênior especializado em Sistemas de Tempo Real.

Você deve implementar um simulador de eventos discretos em **Python**. O objetivo não é executar as tarefas de verdade, mas simular matematicamente o comportamento temporal delas. O tempo não deve avançar passo-a-passo (`t++`), mas sim **saltar** (`t += dt`) para o próximo evento relevante (Chegada ou Término).

**Requisitos Críticos:**

1. **Linguagem:** Python.
2. **Paradigmas:** Orientação a Objetos e Clean Code.
3. **Saída:** Gráfico de Gantt em ASCII no terminal.
4. **Simplicidade:** Sem bibliotecas gráficas pesadas (apenas *built-ins* ou leves).

---

## 1. Arquitetura de Classes (Domain Model)

Implemente as seguintes estruturas de dados para garantir a integridade do estado.

### 1.1. Classe `Task` (Imutável)

Representa a definição estática da tarefa.

* **Atributos:**
* `id`: (str) Identificador (ex: "T1").
* `period`: (int) Período . Assuma .
* `execution_time`: (int) Custo computacional .

* **Propriedades:**
* `priority`: (int) Baseado no Rate Monotonic ( menor = Prioridade maior).
* `utilization`: (float) .

### 1.2. Classe `Job` (Dinâmico)

Representa uma instância ativa de uma tarefa em um momento específico.

* **Atributos:**
* `task`: Referência ao objeto `Task`.
* `id`: (int) Número da instância (Job 1, Job 2...).
* `arrival_time`: (float) Instante de chegada absoluta.
* `remaining_time`: (float) Tempo de execução restante. Inicializa com `task.execution_time`.
* `absolute_deadline`: (float) `arrival_time + task.period`.
* `completed`: (bool) Flag de conclusão.

### 1.3. Classe `Processor`

Representa um núcleo de processamento.

* **Atributos:**
* `id`: (int).
* `assigned_tasks`: (List[Task]) Lista de tarefas alocadas neste núcleo (usado no Multiprocessador).
* `active_job`: (Job | None) O job sendo executado atualmente.
* `ready_queue`: (List[Job]) Fila de prontos, deve ser **sempre ordenada pela Prioridade RM**.
* `execution_log`: (List) Tuplas `(start_time, end_time, task_id)` para desenhar o Gantt.

---

## 2. Lógica dos Algoritmos (Core Logic)

### 2.1. Rate Monotonic (RM) - Uniprocessador

* **Escopo:** Nível de Processador.
* **Regra:** Selecionar sempre o Job na `ready_queue` cuja `Task` tenha o **menor período**.
* **Preempção:** Total. Se um Job chega e tem período menor que o Job atual, o atual sofre preempção (volta para a fila) e o novo assume.

### 2.2. First-Fit Rate Monotonic (FF-RM) - Multiprocessador

* **Escopo:** Fase de Configuração (Antes da Simulação).
* **Estratégia:** Particionamento (Bin Packing).
* **Algoritmo:**
1. Ordene todas as `Tasks` globais por prioridade RM (Menor período primeiro).
2. Instancie uma lista de `Processors` (comece com 1).
3. Para cada `Task`:
* Tente alocar no Processador 1.
* **Teste de Admissibilidade (Liu & Layland):** Uma tarefa cabe se a utilização total do processador , onde  é o número de tarefas naquele processador.
* Se couber, adicione à lista `assigned_tasks` do processador.
* Se não couber, tente no próximo. Se não houver próximo, crie um novo Processador.

4. Após o particionamento, cada processador roda sua simulação independentemente.

---

## 3. O Motor de Simulação (Discrete Event Engine)

Esta é a parte mais importante para evitar erros de lógica temporal. Não use loops fixos. Use cálculo de Delta ().

**Fluxo Principal (Método `run_simulation`):**

1. **Setup:**
* Tempo atual (`current_time`) = 0.
* Tempo máximo (`max_time`) = MMC (Mínimo Múltiplo Comum) dos períodos das tarefas (Hyperperiod).
* Gere o primeiro Job (chegada em 0) para todas as tarefas alocadas.

2. **Loop (`while current_time < max_time`):**
* **Passo A: Encontrar o Próximo Evento**
* `next_arrival`: Menor tempo de chegada futura entre todas as tarefas.
* `next_completion`: Para cada processador, se houver `active_job`, calcule: `current_time + active_job.remaining_time`. Pegue o menor.
* `next_event_time`: O menor valor entre `next_arrival` e `next_completion`.
* Se `next_event_time` > `max_time`, pare.

* **Passo B: Avançar o Estado (Cálculo do Delta)**
* `dt = next_event_time - current_time`
* Para cada processador com `active_job`:
* Decrementar `active_job.remaining_time` em `dt`.
* Registrar execução no `execution_log` (intervalo `current_time` a `next_event_time`).

* `current_time = next_event_time`.

* **Passo C: Tratar Eventos**
* **Chegadas:** Se `current_time` == tempo de chegada de uma tarefa, crie o novo `Job`, adicione na `ready_queue` do processador correto e calcule a *próxima* chegada dessa tarefa.
* **Conclusões:** Se algum `active_job.remaining_time <= 0`:
* Marque como `completed`.
* Remova do processador (`active_job = None`).

* **Passo D: Escalonamento (Dispatcher)**
* Para cada processador:
* Se houver um `active_job` mas existir alguém na fila com maior prioridade (preempção), mova o `active_job` de volta para a fila.
* Ordene a `ready_queue` (Menor Período primeiro).
* Se processador livre e fila não vazia: Pop no primeiro da fila  `active_job`.

---

## 4. Visualização (Diagrama de Gantt ASCII)

Implemente uma função `print_gantt(processors, max_time)` que gera o gráfico.

**Formato Esperado:**

```text
Tempo:  0    1    2    3    4    5    6 ...
      |----|----|----|----|----|----|...
CPU 0: [T1 ][T1 ][T2 ][   ][T1 ][T1 ]...
CPU 1: [T3 ][T3 ][T3 ][T4 ][T4 ][   ]...

```

* Use caracteres simples.
* Represente "Idle" (Ocioso) com espaços vazios ou `_`.
* Represente conflitos/perda de deadline (Overrun) com um símbolo de alerta (ex: `!`) se necessário.

---

## 5. Exemplo de Execução (Test Case)

Para validar se a IA implementou corretamente, peça para rodar o seguinte cenário no final do código:

* **Algoritmo:** First-Fit RM (Multiprocessador).
* **Tarefas:**
1. T1 (C=1, T=2) - Alta utilização (0.5)
2. T2 (C=2, T=5) - Média (0.4)
3. T3 (C=2, T=4) - Média (0.5)

* **Comportamento esperado:**
* T1 (U=0.5) e T2 (U=0.4) devem tentar ficar no Proc 1 (Total 0.9). O limite de Liu & Layland para 2 tarefas é ~0.828.
* Dependendo da implementação estrita de LL, T2 pode ser jogada para o Proc 2. Se usar apenas , ficam juntas. *Instrução: Use Liu & Layland estrito para garantir segurança Hard Real-Time.*

---

**Instrução Final para a IA:**
"Gere apenas o código Python completo, contido em um único arquivo ou estrutura modular clara. Não explique a teoria novamente, foque na implementação robusta do plano acima."
