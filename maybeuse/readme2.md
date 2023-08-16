
![Project Logo](https://manggalla.com/beta/wp-content/uploads/2023/02/Logo-SMR-1.png)

---

# Python Script Collection

A collection of Python scripts for various tasks, including data processing, SQL query generation, and more.

## Table of Contents

- [Introduction](#introduction)
- [Scripts](#scripts)
  - [validatemac.py](#validatemacpy)
  - [validatewindows.py](#validatewindowspy)
  - [fetch_PO.py](#fetch_popy)
  - [balikansf.py](#balikansfpy)
  - [invoice_time.py](#invoice_timepy)
  - [main.py](#mainpy)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This repository contains a collection of Python scripts designed to perform various tasks, from data validation and processing to SQL query generation. Each script serves a specific purpose and can be used individually or as part of a larger workflow.

## Scripts

### validatemac.py

This script reads MAC addresses from a CSV file, validates them, and generates SQL queries for insertion into a database. It calculates business days, generates timestamps, and handles customer-specific logic.

### validatewindows.py

A GUI-based script that validates passwords using a hashed comparison. It prompts users for a password, checks it against a stored hash, and performs actions accordingly. It also generates SQL queries for insertion based on user input.

### fetch_PO.py

This script cleans and processes data from a CSV file, extracting relevant information. It allows users to filter data based on specific criteria and generates SQL queries for insertion into a database.

### balikansf.py

Reads data from a CSV file, transforms it by creating new rows for different document types, and generates SQL queries for insertion into a database. Transformed data is copied to the clipboard, and the original CSV file is removed.

### invoice_time.py

A GUI application that generates SQL UPDATE queries for updating 'invoice_time' in CSV data. Users can pick a CSV file, generate the query, and copy it to the clipboard. The selected CSV file is deleted after generating the query.

### main.py

This script demonstrates generating SQL queries from data processing to insertion. It reads data, performs transformations, and generates SQL queries for insertion into database tables.

## Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. Navigate to the relevant script's directory:
   ```bash
   cd script-directory
   ```

3. Install any required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the script:
   ```bash
   python script-name.py
   ```

## Contributing

Contributions to this collection of Python scripts are welcome. If you find a bug or want to add a new feature, feel free to open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
```

Replace `yourusername/your-repo` with your actual GitHub repository's URL, and modify the script descriptions and usage instructions accordingly. Additionally, make sure to include the appropriate license file (e.g., `LICENSE.txt`) in your repository.

This README.md template provides an organized and informative overview of your Python script collection, making it easy for users to understand the purpose of each script and how to use them.