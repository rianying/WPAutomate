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
- `scripts/balikandepo.py`: Handles the operations related to depot returns or depot management.
- `scripts/balikanidm.py`: Manages tasks associated with Internet Download Manager operations.
- `scripts/balikansat.py`: Automates processes for satellite-related operations or equipment management.
- `scripts/balikansd.py`: Deals with operations involving SD card storage or related functionalities.
- `scripts/balikansf.py`: A script with a specific function within the automation process, details to be added upon clarification.
- `scripts/monitor.py`: Monitors the status and health of various automated processes.
- `scripts/newcustomer.py`: Automates the onboarding process for new customers.
- `scripts/preorder.py`: Manages the pre-ordering system, from taking orders to processing them.
- `scripts/validate.py`: Validates data or process integrity before proceeding with automation tasks.

## Installation

To install the required dependencies for WPAutomate, run the following command:

```bash
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
