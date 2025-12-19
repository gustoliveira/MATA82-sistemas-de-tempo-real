from main import Task, Processor, run_simulation, print_gantt

def test_custom_scenario():
    # Task(id, period, execution_time)
    # T1: C=2, T=9 -> period=9, exec=2
    # T2: C=2, T=5 -> period=5, exec=2
    # T3: C=1, T=3 -> period=3, exec=1
    
    tasks = [
        Task("T1", 9, 2), # Baixa Prioridade (Maior período)
        Task("T2", 5, 2), # Média Prioridade
        Task("T3", 3, 1)  # Alta Prioridade (Menor período)
    ]

    print("\n" + "="*60)
    print("TESTE CUSTOMIZADO: Uniprocessador RM")
    print("="*60)
    print(f"Tarefas: {[str(t) for t in tasks]}")

    # Configurar Processador Único
    cpu = Processor(0)
    for t in tasks:
        cpu.add_task(t)

    # Executar Simulação
    duration = 10
    print(f"\nRodando simulação por {duration} unidades de tempo...")
    
    run_simulation([cpu], duration)
    print_gantt([cpu], duration)

if __name__ == "__main__":
    test_custom_scenario()

