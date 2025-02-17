import sqlite3
from collections import defaultdict
from typing import Dict, List, Tuple
from z3 import *

class PipelineOptimizer:
    def __init__(self, db_name: str = "benchmark_results.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def get_execution_times(self, machine: str, application: str) -> Dict:
        """Get minimum execution times for each stage on each core type/backend."""
        query = """
            SELECT stage, backend, core_type, MIN(time_ms) as min_time
            FROM benchmark_result
            WHERE machine_name = ? AND application = ? AND stage > 0
            GROUP BY stage, backend, core_type
            HAVING min_time IS NOT NULL
            ORDER BY stage, backend, core_type
        """
        self.cursor.execute(query, (machine, application))
        
        times = defaultdict(lambda: defaultdict(dict))
        for stage, backend, core_type, time in self.cursor.fetchall():
            if backend in ['CUDA', 'VK'] or core_type == 'None':
                times[stage][backend] = float(time)
            else:
                times[stage][backend][core_type] = float(time)
        return times

    def get_machine_resources(self, machine: str, application: str) -> Tuple[List[str], List[str]]:
        """Get available backends and core types for a machine and application."""
        # Get backends filtered by machine and application.
        self.cursor.execute("""
            SELECT DISTINCT backend 
            FROM benchmark_result 
            WHERE machine_name = ? AND application = ? AND backend IS NOT NULL
        """, (machine, application))
        backends = [row[0] for row in self.cursor.fetchall()]

        # Get core types filtered by machine and application.
        self.cursor.execute("""
            SELECT DISTINCT core_type 
            FROM benchmark_result 
            WHERE machine_name = ? AND application = ? 
              AND core_type IS NOT NULL AND core_type != 'None'
        """, (machine, application))
        core_types = [row[0] for row in self.cursor.fetchall()]

        return backends, core_types

    def optimize_pipeline(self, machine: str, application: str) -> Dict:
        """Find optimal pipeline configuration using Z3."""
        # Get execution times and resources
        times = self.get_execution_times(machine, application)
        if not times:
            return None
            
        stages = sorted(times.keys())
        backends, core_types = self.get_machine_resources(machine, application)

        # Create Z3 optimizer
        solver = Optimize()
        
        # Create variables for stage assignments.
        # For GPU-like backends (e.g. CUDA, VK) we use a Bool for each stage.
        # For CPU backends, we use a Bool for each core type option.
        assign = {}
        for s in stages:
            assign[s] = {}
            for b in backends:
                if b in ['CUDA', 'VK']:
                    assign[s][b] = Bool(f's{s}_{b}')
                else:
                    assign[s][b] = {}
                    for c in core_types:
                        assign[s][b][c] = Bool(f's{s}_{b}_{c}')

        # Constraint 1: Each stage must be assigned exactly one resource.
        for s in stages:
            stage_assignments = []
            for b in backends:
                if b in ['CUDA', 'VK']:
                    stage_assignments.append(assign[s][b])
                else:
                    stage_assignments.extend(list(assign[s][b].values()))
            solver.add(PbEq([(a, 1) for a in stage_assignments], 1))

        # Constraint 2: Must use all resources (each GPU backend and each CPU core type)
        for b in backends:
            if b in ['CUDA', 'VK']:
                solver.add(Or([assign[s][b] for s in stages]))
            else:
                for c in core_types:
                    solver.add(Or([assign[s][b][c] for s in stages]))

        # Constraint 3: Enforce contiguous (grouped) usage of each resource.
        # Once a resource is dropped, it cannot reappear later.
        for b in backends:
            if b in ['CUDA', 'VK']:
                for i in range(len(stages) - 1):
                    s_i = stages[i]
                    s_ip1 = stages[i+1]
                    solver.add(
                        Implies(
                            And(assign[s_i][b], Not(assign[s_ip1][b])),
                            And([Not(assign[stages[j]][b]) for j in range(i+2, len(stages))])
                        )
                    )
            else:
                for c in core_types:
                    for i in range(len(stages) - 1):
                        s_i = stages[i]
                        s_ip1 = stages[i+1]
                        solver.add(
                            Implies(
                                And(assign[s_i][b][c], Not(assign[s_ip1][b][c])),
                                And([Not(assign[stages[j]][b][c]) for j in range(i+2, len(stages))])
                            )
                        )

        # Calculate total execution time as the sum over stages.
        total_time = Real('total_time')
        time_terms = []
        for s in stages:
            stage_terms = []
            for b in backends:
                if b in ['CUDA', 'VK']:
                    if b in times[s]:
                        stage_terms.append(
                            If(assign[s][b], times[s][b], 0.0)
                        )
                else:
                    for c in core_types:
                        if c in times[s][b]:
                            stage_terms.append(
                                If(assign[s][b][c], times[s][b][c], 0.0)
                            )
            time_terms.extend(stage_terms)

        solver.add(total_time == Sum(time_terms))
        solver.minimize(total_time)

        # Solve and extract the solution.
        if solver.check() == sat:
            model = solver.model()
            solution = {}
            total_time_str = model.evaluate(total_time).as_decimal(10)
            if total_time_str.endswith('?'):
                total_time_str = total_time_str[:-1]
            total_time_value = float(total_time_str)
            
            for s in stages:
                for b in backends:
                    if b in ['CUDA', 'VK']:
                        if is_true(model.evaluate(assign[s][b])):
                            solution[s] = (b, None, times[s][b])
                            break
                    else:
                        for c in core_types:
                            if is_true(model.evaluate(assign[s][b][c])):
                                solution[s] = (b, c, times[s][b][c])
                                break
            
            return {
                'pipeline': solution,
                'total_time': total_time_value  # This is the latency (sum of all stage times)
            }
        
        return None

    def print_pipeline_report(self):
        """Print optimized pipeline configurations for all devices and applications."""
        print("=== Pipeline Optimization Report ===\n")
        
        # Get all machines.
        self.cursor.execute("SELECT DISTINCT machine_name FROM benchmark_result")
        machines = [row[0] for row in self.cursor.fetchall()]
        
        for machine in sorted(machines):
            print(f"Device: {machine}")
            
            # Get applications for the device.
            self.cursor.execute(
                "SELECT DISTINCT application FROM benchmark_result WHERE machine_name = ?",
                (machine,)
            )
            applications = [row[0] for row in self.cursor.fetchall()]
            
            for app in sorted(applications):
                print(f"\nApplication: {app}")
                result = self.optimize_pipeline(machine, app)
                
                if result:
                    # Print grouped format first.
                    print("\nOptimal Pipeline (Grouped):")
                    current_backend = None
                    current_core = None
                    for stage in sorted(result['pipeline'].keys()):
                        backend, core, time = result['pipeline'][stage]
                        if (backend, core) != (current_backend, current_core):
                            core_str = f" ({core} cores)" if core else ""
                            print(f"\n- {backend}{core_str}:")
                            current_backend = backend
                            current_core = core
                        print(f"  Stage {stage:<2} ({time:6.2f} ms)")
                    
                    # Print stage-by-stage format.
                    print("\nOptimal Pipeline (Stage by Stage):")
                    for stage in sorted(result['pipeline'].keys()):
                        backend, core, time = result['pipeline'][stage]
                        core_str = f" ({core} cores)" if core else ""
                        print(f"Stage {stage:<2} ({time:6.2f} ms) {backend}{core_str}")
                    
                    print(f"\nTotal execution time for one iteration (latency): {result['total_time']:.2f} ms")
                    
                    # ---- New: Pipeline Iteration Simulation ----
                    iterations = 5
                    # Group contiguous stages with the same resource allocation.
                    grouped_pipeline = []
                    sorted_stages = sorted(result['pipeline'].keys())
                    current_resource = None
                    current_group_time = 0.0
                    for s in sorted_stages:
                        backend, core, time = result['pipeline'][s]
                        resource_id = (backend, core)
                        if current_resource is None:
                            current_resource = resource_id
                            current_group_time = time
                        else:
                            if resource_id == current_resource:
                                current_group_time += time
                            else:
                                grouped_pipeline.append((current_resource, current_group_time))
                                current_resource = resource_id
                                current_group_time = time
                    if current_resource is not None:
                        grouped_pipeline.append((current_resource, current_group_time))
                    
                    # Compute pipeline latency and cycle time.
                    latency = sum(group_time for (_, group_time) in grouped_pipeline)
                    cycle_time = max(group_time for (_, group_time) in grouped_pipeline)
                    
                    print("\nIteration Timing Simulation (Pipelined Execution):")
                    print(f"Pipeline Latency (first iteration): {latency:.2f} ms")
                    print(f"Pipeline Cycle Time (steady state): {cycle_time:.2f} ms")
                    total_pipeline_time = latency + (iterations - 1) * cycle_time
                    for i in range(1, iterations + 1):
                        if i == 1:
                            finish_time = latency
                        else:
                            finish_time = latency + (i - 1) * cycle_time
                        print(f"Iteration {i}: finish at {finish_time:.2f} ms")
                    print(f"Total time for {iterations} iterations: {total_pipeline_time:.2f} ms")
                    # ---- End of Iteration Simulation ----
                    
                else:
                    print("Could not find valid pipeline configuration")
            
            print("\n" + "="*50)

    def __del__(self):
        self.conn.close()

def main():
    optimizer = PipelineOptimizer()
    optimizer.print_pipeline_report()

if __name__ == "__main__":
    main()

