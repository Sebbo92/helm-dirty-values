# Overview
This Helm plugin checks for unused keys in a Helm chart's `values.yaml` and additional yaml files by scanning the `templates` directory for references to those keys.

## Features
- Parses the `values.yaml` file and additional values files to extract all keys, including nested keys.
- Scans all `.yaml` and `.tpl` files in the `templates` directory for references to `Values.<key>`.
- Identifies unused keys in `values.yaml` and additional values files.
- Groups unused keys by their source file for better clarity.

## Requirements
- Helm 3.x
- Python 3.x

## Installation
Run the command `helm plugin install https://github.com/Sebbo92/helm-dirty-values`. A .venv will be created and required modules from [requirements.txt](./requirements.txt) will be installed.

## Usage
```bash
helm dirty-values main.py [-h] --chart CHART [--additional-value-file ADDITIONAL_VALUE_FILE]
# Example within this repository
helm dirty-values --chart test --additional-value-file test.yaml

# Output
Unused keys in values.yaml:
  - test.super
Unused keys in test.yaml:
  - alpha
  - list
```
