![Project Logo](https://manggalla.com/beta/wp-content/uploads/2023/02/Logo-SMR-1.png)
# WPAutomate

WPAutomate is a collection of scripts designed to automate SMR's OSC Intern Jobs. This repository contains scripts for environment setup, main application logic, and specific automated tasks such as handling depot operations, managing new customers, and processing pre-orders.

## Scripts

### Environment Setup
- `env/env.py`: Manages environment variables and configurations for the automation scripts.

### Main Application
- `main.py`: Serves as the entry point for executing the automated tasks defined in the scripts.

### Dependencies
- `requirements.txt`: Contains all the necessary Python packages required to run the scripts.

### Automated Tasks
- `scripts/balikandepo.py`: Handles the documents associated with depo and have it ready to paste into excel.
- `scripts/balikanidm.py`: Handles the documents associated with IDM and have it ready to paste into excel.
- `scripts/balikansat.py`: Handles the documents associated with SAT and have it ready to paste into excel.
- `scripts/balikansd.py`: Handles the documents associated with SD and have it ready to paste into excel.
- `scripts/balikansf.py`: Handles the documents associated with SF and have it ready to paste into excel.
- `scripts/monitor.py`: Monitors the status and health of various automated processes.
- `scripts/preorder.py`: Manages the pre-ordering system, from taking orders to processing them.
- `scripts/validate.py`: Validates data or process integrity before proceeding with automation tasks.

## Installation

To install the required dependencies for WPAutomate, run the following command on terminal / command prompts:

```bash
#For MacOS / Linux
python3 -m venv ./venv
#Activating virtual environment
source .venv/bin/activate

#For Windows
python -m .venv/Scripts/Activate
#Activating virtual environment
./venv/bin/activate
```

To deactivate virtual environment, simply run the following command:
```bash
deactivate
```

```bash
#For MacOS / Linux
pip3 install -r requirements.txt

#For Windows
pip install -r requirements.txt
```

## Usage

To use the automation scripts, set up the necessary environment variables in `env/env.py` and execute `main.py`

```bash
python main.py
```

## Contributing

Contributions to WPAutomate are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Author

`Rahmadiyan Muhammad`

- Porto: [https://rian.social
- Medium: [https://medium.com/@rianying
- Linkedin: [https://www.linkedin.com/in/rahmadiyanmuhammad/
