import os
import yaml
import re
import argparse
from collections import defaultdict

def load_values_yaml(values_file):
    with open(values_file, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def merge_dicts(base, updates, source_map, source_file, prefix=""):
    """
    Recursively merge two dictionaries. Values from `updates` overwrite `base`.
    Tracks the source of each key in `source_map`.
    """
    source_filename = os.path.basename(source_file)  # Extract only the filename
    for key, value in updates.items():
        full_key = f"{prefix}.{key}" if prefix else key
        source_map[full_key] = source_filename  # Store only the filename
        if isinstance(value, dict):
            # Ensure the base dictionary has the same structure
            if key not in base or not isinstance(base[key], dict):
                base[key] = {}
            merge_dicts(base[key], value, source_map, source_file, full_key)
        else:
            base[key] = value

def find_unused_keys(values, templates_dir, source_map):
    unused_keys = []

    # Flatten the nested dictionary keys
    def flatten_keys(d, prefix=''):
        keys = []
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.extend(flatten_keys(v, full_key))
            else:
                keys.append(full_key)
        return keys

    flattened_keys = flatten_keys(values)

    # Search for each key in the templates
    used_keys = set()
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith((".yaml", ".tpl")):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as template_file:
                    content = template_file.read()
                    for key in flattened_keys:
                        # Check if the key or any parent key is used
                        key_parts = key.split('.')
                        for i in range(len(key_parts)):
                            parent_key = '.'.join(key_parts[:i + 1])
                            key_pattern = re.compile(rf"\bValues\.{re.escape(parent_key)}\b")
                            if key_pattern.search(content):
                                used_keys.add(key)
                                break

    # Find unused keys
    unused_keys = [key for key in flattened_keys if key not in used_keys]

    # Map unused keys to their source files
    unused_keys_with_sources = [(key, source_map.get(key, "unknown source")) for key in unused_keys]

    return unused_keys_with_sources

def main():
    parser = argparse.ArgumentParser(description="Check unused keys in Helm values.yaml.")
    parser.add_argument("--chart", required=True, help="Path to the Helm chart directory")
    parser.add_argument(
        "--additional-value-file",
        action="append",
        help="Name of additional values-*.yaml files in the chart directory (can be specified multiple times)"
    )
    args = parser.parse_args()

    chart_path = args.chart
    values_file = os.path.join(chart_path, "values.yaml")
    templates_dir = os.path.join(chart_path, "templates")

    if not os.path.exists(values_file):
        print(f"Values file '{values_file}' not found.")
        return

    if not os.path.exists(templates_dir):
        print(f"Templates directory '{templates_dir}' not found.")
        return

    # Load the base values.yaml
    values = load_values_yaml(values_file)
    source_map = {}
    # Ensure the source_map is populated with the correct path for values.yaml
    merge_dicts({}, values, source_map, values_file)

    # Merge additional values files if provided
    if args.additional_value_file:
        for additional_file in args.additional_value_file:
            additional_file_path = os.path.join(chart_path, additional_file)
            if not os.path.exists(additional_file_path):
                print(f"Additional values file '{additional_file}' not found in chart directory.")
                continue
            additional_values = load_values_yaml(additional_file_path)
            merge_dicts(values, additional_values, source_map, additional_file_path)

    # Find unused keys
    unused_keys_with_sources = find_unused_keys(values, templates_dir, source_map)

    if unused_keys_with_sources:
        # Group unused keys by their source file
        grouped_unused_keys = defaultdict(list)
        for key, source in unused_keys_with_sources:
            grouped_unused_keys[source].append(key)

        for source, keys in grouped_unused_keys.items():
            print(f"Unused keys in {source}:")
            for key in keys:
                print(f"  - {key}")
    else:
        print("All keys in values.yaml are used in the templates.")

if __name__ == "__main__":
    main()
