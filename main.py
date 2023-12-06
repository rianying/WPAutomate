import subprocess
import glob
import os
import argparse

# Define the path to the scripts directory
scripts_dir = os.path.join(os.getcwd(), "scripts")


def get_script_description(path):
    # Open the script and read the first few lines
    with open(path, "r") as file:
        lines = file.readlines()
    # Look for a docstring at the start of the file enclosed in triple quotes
    description_lines = []
    reading_description = False
    for line in lines:
        line = line.strip()
        if line.startswith('"""'):  # Check if line is the start of a docstring
            if reading_description:  # Check if it's the end of the docstring
                break
            else:
                reading_description = True  # Mark the start of the docstring
                continue  # Skip the line with starting quotes
        if reading_description:  # If within docstring, append the line
            description_lines.append(line)
    return " ".join(description_lines) or "No description available."


def list_scripts():
    # Use glob to find all .py files in the scripts directory
    script_paths = sorted(glob.glob(os.path.join(scripts_dir, "*.py")))
    script_names = [
        os.path.basename(path) for path in script_paths
    ]  # Extract file names

    print("\n\nWhich script do you want to run?\n")
    for i, script_name in enumerate(script_names, start=1):
        # Get the full path of script
        full_script_path = os.path.join(scripts_dir, script_name)
        # Get the description for each script
        description = get_script_description(full_script_path)
        # Print the script name with its description
        print(
            f"{i}. {script_name[:-3]} \t|{description}\n"
        )  # Remove the .py extension for display
    print("\n")
    return script_paths


def run_script(script_path):
    try:
        # Run the script using its full path
        subprocess.run(["python3", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running the script: {script_path}")
        print(e)


def show_help():
    # Function to display help message
    parser.print_help()
    list_scripts()  # Optionally display available scripts after showing help


if __name__ == "__main__":
    # Set up argparse to accept a script name as an optional argument
    parser = argparse.ArgumentParser(
        description="Run a specified script or display a menu to choose one."
    )
    parser.add_argument(
        "script_name",
        nargs="?",
        help="The name of the script to run without the .py extension",
        default=None,
    )
    args = parser.parse_args()

    # Adjust the logic to check for .py extension
    if args.script_name:
        # Add the .py extension if it's not already there
        script_name_with_extension = (
            args.script_name
            if args.script_name.endswith(".py")
            else f"{args.script_name}.py"
        )
        script_path = os.path.join(scripts_dir, script_name_with_extension)

        if os.path.isfile(script_path):
            run_script(script_path)
        else:
            print(
                f"Script {script_name_with_extension} does not exist or is not a .py file."
            )
    else:
        # Interactive prompt to choose a script to run
        while True:
            script_paths = list_scripts()
            try:
                choice = input("Enter the number of the script (0 to exit): ")
                if choice == "0":
                    break
                choice = int(choice)  # Convert input to int for selection
                if 1 <= choice <= len(script_paths):
                    script_to_run = script_paths[choice - 1]
                    run_script(script_to_run)
                else:
                    print("Invalid choice. Please enter a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
