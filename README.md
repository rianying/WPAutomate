### README.md

![Project Logo](https://manggalla.com/beta/wp-content/uploads/2023/02/Logo-SMR-1.png)

---

## Personal Automation: SQL Query Generator

Welcome to my personal project! As part of my daily job, I found myself spending a lot of time on manual tasks. To optimize this process, I created this Python script that automates the generation of SQL queries from Excel data.

### Project Purpose:
- **Reduce Manual Work**: By automating the conversion of Excel data into SQL queries, I've significantly reduced the time spent on manual data entry.
- **Increase Accuracy**: Automation ensures consistent and error-free SQL query generation.

### Requirements:
- Python 3
- Libraries: `pandas`, `numpy`, `datetime`

### Features:
1. **Business Days Calculation**: Computes a date by adding a specified number of business days to a given date.
2. **Automated SQL Query Generation**: Uses Excel data to generate SQL queries for three specific tables, ensuring consistent data formatting and handling.

### How to Use:
1. Install the required libraries:
```
pip install pandas numpy
```
2. Place your Excel data file in the same directory as the script and name it `preorder.xlsx`. Alternatively, you can modify the script to use a different file name/path.
3. Execute the script:
```
python mainformac.py
```
4. When prompted, provide the order time in the format `YYYY-MM-DD HH:MM:SS`.
5. The script will output SQL queries tailored to the data provided.

### Notes:
- Always ensure that the Excel file columns (`No PO`, `No SO`, and `Customer Name`) are correctly formatted.
- It's good practice to review the generated SQL queries before executing them on a live database to ensure accuracy.

Thank you for checking out my project! I hope it serves as an inspiration for others looking to streamline their daily tasks.

---

## Author

`Rahmadiyan Muhammad`

- Porto: [https://rian.social
- Medium: [https://medium.com/@rianying
- Linkedin: [https://www.linkedin.com/in/rahmadiyanmuhammad/
