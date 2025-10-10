import os
import yaml
import re
import argparse
import sys

def verify_chart_path(chart_path):
    """
    Verify that the provided chart path is valid.
    Return chart_path if valid, otherwise exit with an error.
    """
    if os.path.isdir(chart_path):
        return chart_path
    else:
        print(f"Error: The chart {chart_path} does not exist.")
        sys.exit(1)

def load_yaml_file(values_file):
    """
    Load and parse the values.yaml from the given chart path.
    Return the parsed yaml file as a dictionary.
    """
    try:
        with open(values_file, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"{e}")
        sys.exit(2)

def load_additional_yaml_files(additional_values):
    """
    Load and parse additional values-*.yaml files.
    Return a list of parsed yaml files as dictionaries.
    """
    values = []
    for file in additional_values:
        values.append(load_yaml_file(file))
    return values

def find_unused_keys(values, templates_dir, source_map=None):
    unused_keys = []

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
    used_keys = set()

    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith((".yaml", ".tpl")):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    for key in flattened_keys:
                        key_parts = key.split('.')
                        for i in range(len(key_parts)):
                            parent_key = '.'.join(key_parts[:i + 1])
                            key_pattern = re.compile(rf"\bValues\.{re.escape(parent_key)}\b")
                            if key_pattern.search(content):
                                used_keys.add(key)
                                break

    unused_keys = [key for key in flattened_keys if key not in used_keys]
    return [(key, None) for key in unused_keys]

def collect_yaml_keys(data, prefix=""):
    keys = set()
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            keys.update(collect_yaml_keys(value, full_key))
    return keys


def extract_used_values_from_templates(templates_dir):
    used_keys = set()
    pattern = re.compile(r'\.Values(?:\.([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*))?')

    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(('.yaml', '.tpl')):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    for match in pattern.findall(content):
                        if match:
                            used_keys.add(match)
                        else:
                            used_keys.add("")  # This handles bare `.Values`
    return used_keys


def merge_dicts(base, updates, source_map, source_file, prefix=""):
    """
    Recursively merge two dictionaries. Values from `updates` overwrite `base`.
    Track the source of each key in `source_map`.
    """
    source_filename = os.path.basename(source_file)
    for key, value in updates.items():
        full_key = f"{prefix}.{key}" if prefix else key
        source_map[full_key] = source_filename
        if isinstance(value, dict):
            # Ensure the base dictionary has the same structure
            if key not in base or not isinstance(base[key], dict):
                base[key] = {}
            merge_dicts(base[key], value, source_map, source_file, full_key)
        else:
            base[key] = value

def find_all_templates_and_values(chart_path):
    """
    Find all templates and values.yaml files in the main chart and its subcharts.
    """
    templates_dirs = []
    values_files = []

    # Hauptchart
    templates_dirs.append(os.path.join(chart_path, "templates"))
    values_files.append(os.path.join(chart_path, "values.yaml"))

    # Subcharts
    subcharts_dir = os.path.join(chart_path, "charts")
    if os.path.exists(subcharts_dir):
        for subchart in os.listdir(subcharts_dir):
            subchart_path = os.path.join(subcharts_dir, subchart)
            if os.path.isdir(subchart_path):
                templates_dirs.append(os.path.join(subchart_path, "templates"))
                values_files.append(os.path.join(subchart_path, "values.yaml"))

    return templates_dirs, values_files

def main():
    parser = argparse.ArgumentParser(description="Check unused keys in Helm values.yaml.")
    parser.add_argument("--chart", required=True, help="Path to the Helm chart directory")
    parser.add_argument(
        "--additional-value-file",
        action="append",
        help="Name of additional values-*.yaml files in the chart directory (can be specified multiple times)"
    )
    args = parser.parse_args()
    chart_path = verify_chart_path(args.chart)
    templates_path = os.path.join(chart_path, "templates")

    default_values_yaml = load_yaml_file(f"{chart_path}/values.yaml")
    unused_keys = find_unused_keys(default_values_yaml, templates_path)
    if unused_keys:
        print(f"Unused keys in values.yaml:")
        for key, _ in unused_keys:
            print(f"  - {key}")
    else:
        print("All keys in values.yaml are used.")

    if args.additional_value_file:
        additional_paths = [os.path.join(chart_path, f) for f in args.additional_value_file]
        additional_values_yamls = load_additional_yaml_files(additional_paths)
        for file_path, values_dict in zip(additional_paths, additional_values_yamls):
            file_name = os.path.basename(file_path)
            unused_keys = find_unused_keys(values_dict, templates_path)
            if unused_keys:
                print(f"Unused keys in {file_name}:")
                for key, _ in unused_keys:
                    print(f"  - {key}")
            else:
                print(f"All keys in {file_name} are used.")
    else:
        print("No additional values files provided.")

if __name__ == "__main__":
    main()
