import pandas as pd
import numpy as np
import subprocess

def list_scripts():
    script_names = [
        "validatemac.py",
        "balikansfall.py",
        "balikansat.py",
        "balikanidm.py",
        "balikandepo.py",
    ]

    print("\n\nWhich script do you want to run?")
    for i, script_name in enumerate(script_names, start=1):
        print(f"{i}. {script_name[:-3]}")
    print('\n')

def run_script(script_name):
    try:
        subprocess.run(['python3', script_name], check=True)
    except subprocess.CalledProcessError:
        print(f"Error running the script: {script_name}")

if __name__ == "__main__":
    while True:
        list_scripts()

        try:
            choice = int(input("Enter the number of the script (0 to exit): "))
            if choice == 0:
                break
            script_names = [
                "validatemac.py",
                "balikansfall.py",
                "balikansat.py",
                "balikanidm.py",
                "balikandepo.py",
            ]
            if 1 <= choice <= len(script_names):
                script_to_run = script_names[choice - 1]
                run_script(script_to_run)
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")