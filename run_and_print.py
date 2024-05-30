import subprocess

def run_script(script_name):
    try:
        result = subprocess.run(['python3', script_name], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error running {script_name}: {str(e)}"

def main():
    print("Running run.py to generate benchmark data...")
    run_output = run_script('run.py full')
    print("Output from run.py:\n", run_output)

    print("Running basic_allocator.py to perform allocation...")
    allocator_output = run_script('basic_allocator.py')
    print("Output from basic_allocator.py:\n", allocator_output)

if __name__ == "__main__":
    main()

