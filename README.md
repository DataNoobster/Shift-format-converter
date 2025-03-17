# Shift Format Converter

A Streamlit-based web application designed to transform old shift-wise weaving data into a new shift format, calculating runtime and total output for looms based on provided Excel data.

## Overview

The **Shift Format Converter** allows users to upload an Excel file containing weaving data (e.g., loom operation details) and converts it into a new shift format (AA and BB shifts). The app processes the data, calculates runtime and total output per loom, and provides a downloadable Excel file with the transformed results. It features an intuitive UI with data previews and user-friendly feedback.

### Features
- Upload Excel files (.xlsx) with weaving data.
- Validates required columns and processes data into new shift formats (AA: 07:00–18:59, BB: 19:00–06:59).
- Calculates runtime and total output per loom and shift.
- Provides a preview of transformed data.
- Allows downloading the processed data as an Excel file.
- Includes a sidebar with instructions and real-time processing feedback.

## Prerequisites

To run this application, ensure you have the following installed:
- Python 3.8 or higher
- Required Python packages (listed in `requirements.txt`):
