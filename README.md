# Overview

This Helm plugin checks for unused keys in a Helm chart's `values.yaml` file by scanning the `templates` directory for references to those keys.

## Features
- Parses the `values.yaml` file and additional values files to extract all keys, including nested keys.
- Scans all `.yaml` and `.tpl` files in the `templates` directory for references to `Values.<key>`.
- Identifies unused keys in `values.yaml` and additional values files.
- Groups unused keys by their source file for better clarity.

## Requirements
- Python 3.13.7 or higher

## Installation
1. Clone this repository or copy the script to your local machine.
2. Install the required Python package:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
```bash
python main.py [-h] --chart CHART [--additional-value-file ADDITIONAL_VALUE_FILE]
python main.py --chart test --additional-value-file test.yaml

# Output
Unused keys in values.yaml:
  - test.super
Unused keys in test.yaml:
  - alpha
  - list
```
