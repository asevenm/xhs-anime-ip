import subprocess
import sys
import time

def run_script(script_name):
    """Runs a python script and waits for it to finish."""
    print(f"\n{'='*50}")
    print(f"🚀 Starting {script_name}...")
    print(f"{'='*50}\n")
    
    try:
        # sys.executable ensures we use the same python interpreter
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"\n✅ {script_name} finished successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {script_name} failed with exit code {e.returncode}.")
        return False
    except Exception as e:
        print(f"\n❌ An error occurred while running {script_name}: {e}")
        return False

def main():
    scripts = [
        "planner.py",
        "painter.py",
        "publisher.py"
    ]
    
    total_start_time = time.time()
    
    for script in scripts:
        success = run_script(script)
        if not success:
            print(f"\n⛔ Pipeline stopped due to failure in {script}.")
            sys.exit(1)
            
        # Optional: Add a small delay between scripts if needed
        time.sleep(1)
        
    total_time = time.time() - total_start_time
    print(f"\n{'='*50}")
    print(f"🎉 All tasks completed successfully in {total_time:.2f} seconds!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
