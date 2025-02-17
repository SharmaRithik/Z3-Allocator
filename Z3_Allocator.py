import sqlite3
import json
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
        self.cursor.execute("""
            SELECT DISTINCT backend 
            FROM benchmark_result 
            WHERE machine_name = ? AND application = ? AND backend IS NOT NULL
        """, (machine, application))
        backends = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("""
            SELECT DISTINCT core_type 
            FROM benchmark_result 
            WHERE machine_name = ? AND application = ? 
              AND core_type IS NOT NULL AND core_type != 'None'
        """, (machine, application))
        core_types = [row[0] for row in self.cursor.fetchall()]

        return backends, core_types

    def get_thread_mapping(self, device: str, application: str) -> dict:
        """
        Query the database for the thread mapping.
        For CPU resources (backend 'OMP'), we query the minimal number of threads per core type.
        For GPU resources (CUDA/VK), we assume 0 threads.
        """
        mapping = {}
        query = """
            SELECT core_type, MIN(num_threads)
            FROM benchmark_result
            WHERE machine_name = ? AND application = ? AND backend = 'OMP'
              AND core_type IS NOT NULL AND core_type != 'None'
            GROUP BY core_type
        """
        self.cursor.execute(query, (device, application))
        for core_type, threads in self.cursor.fetchall():
            mapping[core_type] = threads
        # For GPU resources, assign 0 threads.
        mapping["gpu"] = 0
        return mapping

    def optimize_pipeline(self, machine: str, application: str) -> Dict:
        """Find optimal pipeline configuration using Z3."""
        times = self.get_execution_times(machine, application)
        if not times:
            return None

        stages = sorted(times.keys())
        backends, core_types = self.get_machine_resources(machine, application)

        solver = Optimize()
        # Create variables for stage assignments.
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

        # Constraint 2: Must use all resources available for this application.
        for b in backends:
            if b in ['CUDA', 'VK']:
                solver.add(Or([assign[s][b] for s in stages]))
            else:
                for c in core_types:
                    solver.add(Or([assign[s][b][c] for s in stages]))

        # Constraint 3: Enforce contiguous (grouped) usage.
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

        # Calculate total execution time.
        total_time = Real('total_time')
        time_terms = []
        for s in stages:
            stage_terms = []
            for b in backends:
                if b in ['CUDA', 'VK']:
                    if b in times[s]:
                        stage_terms.append(If(assign[s][b], times[s][b], 0.0))
                else:
                    for c in core_types:
                        if c in times[s][b]:
                            stage_terms.append(If(assign[s][b][c], times[s][b][c], 0.0))
            time_terms.extend(stage_terms)
        solver.add(total_time == Sum(time_terms))
        solver.minimize(total_time)

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
                'total_time': total_time_value
            }
        return None

    def build_schedule(self, device: str, application: str, result: Dict) -> Dict:
        """
        Build the schedule dictionary with the following format:
        {
          "schedule": {
            "schedule_id": "<device>_<application>_schedule_001",
            "device_id": "<device>",
            "chunks": [
              {
                "name": "chunk1",
                "hardware": "big" or "gpu" or "medium" or "little",
                "threads": <number>,
                "stages": [stage numbers]
              },
              ...
            ]
          },
          "total_time": <total_time>,
          "max_chunk_time": <max_chunk_time>
        }
        """
        pipeline = result["pipeline"]
        sorted_stages = sorted(pipeline.keys())
        grouped_pipeline = []
        current_resource = None
        current_group_time = 0.0
        current_group_stages = []
        for s in sorted_stages:
            backend, core, time_val = pipeline[s]
            resource_id = (backend, core)
            if current_resource is None:
                current_resource = resource_id
                current_group_time = time_val
                current_group_stages = [s]
            else:
                if resource_id == current_resource:
                    current_group_time += time_val
                    current_group_stages.append(s)
                else:
                    grouped_pipeline.append((current_resource, current_group_time, current_group_stages))
                    current_resource = resource_id
                    current_group_time = time_val
                    current_group_stages = [s]
        if current_resource is not None:
            grouped_pipeline.append((current_resource, current_group_time, current_group_stages))
        
        max_chunk_time = max(group_time for (_, group_time, _) in grouped_pipeline) if grouped_pipeline else 0.0
        total_time = result["total_time"]

        # Get thread mapping dynamically from the database.
        thread_mapping = self.get_thread_mapping(device, application)
        
        chunks = []
        chunk_index = 1
        for (resource, group_time, stage_list) in grouped_pipeline:
            backend, core = resource
            if backend in ['CUDA', 'VK']:
                hardware = "gpu"
            else:
                hardware = core  # e.g. "big", "medium", "little"
            threads = thread_mapping.get(hardware, 0)
            chunk = {
                "name": f"chunk{chunk_index}",
                "hardware": hardware,
                "threads": threads,
                "stages": stage_list
            }
            chunks.append(chunk)
            chunk_index += 1

        schedule_dict = {
            "schedule": {
                "schedule_id": f"{device}_{application}_schedule_001",
                "device_id": device,
                "chunks": chunks
            },
            "total_time": total_time,
            "max_chunk_time": max_chunk_time
        }
        return schedule_dict

    def collect_and_save_all_schedules(self):
        """Collect schedules for all device-application combinations and save to a single JSON file."""
        all_schedules = []
        self.cursor.execute("SELECT DISTINCT machine_name FROM benchmark_result")
        machines = [row[0] for row in self.cursor.fetchall()]
        
        for machine in sorted(machines):
            self.cursor.execute(
                "SELECT DISTINCT application FROM benchmark_result WHERE machine_name = ?",
                (machine,)
            )
            applications = [row[0] for row in self.cursor.fetchall()]
            for app in sorted(applications):
                result = self.optimize_pipeline(machine, app)
                if result:
                    schedule_dict = self.build_schedule(machine, app, result)
                    all_schedules.append(schedule_dict)
        with open("all_schedules.json", "w") as f:
            json.dump(all_schedules, f, indent=2)
        print("Saved the combination in file all_schedules.json")

    def __del__(self):
        self.conn.close()

def main():
    optimizer = PipelineOptimizer()
    optimizer.collect_and_save_all_schedules()

if __name__ == "__main__":
    main()

