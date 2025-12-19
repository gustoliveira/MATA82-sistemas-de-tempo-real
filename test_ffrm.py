from main import Task, partition_tasks_ff_rm, run_simulation, print_gantt

def test_ffrm_scenario():
    # Task(id, period, execution_time)
    tasks = [
        Task("T1", 2, 1), # U = 0.5
        Task("T2", 2, 1), # U = 0.5
        Task("T3", 5, 4)  # U = 0.8
    ]

    print("\n" + "="*60)
    print("TESTE CUSTOMIZADO: Multiprocessador FF-RM")
    print("="*60)
    
    # 1. Particionamento
    processors = partition_tasks_ff_rm(tasks)
    
    for proc in processors:
        print(f"CPU {proc.id}: {[str(t) for t in proc.assigned_tasks]} (U={proc.utilization:.2f})")

    # 2. Execução
    duration = 6
    print(f"\nRodando simulação por {duration} unidades de tempo...")
    
    run_simulation(processors, duration)
    print_gantt(processors, duration)

if __name__ == "__main__":
    test_ffrm_scenario()

