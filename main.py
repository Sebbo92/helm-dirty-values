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

def find_unused_keys(values, templates_dir, file_name=None):
    """
    Find unused keys in the provided values dictionary by checking against
    the Helm templates in the specified directory.
    Return a list of unused keys.
    """
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

    if file_name is not None:
        if unused_keys:
            print(f"Unused keys in {file_name}:")
            for key in unused_keys:
                print(f"  - {key}")
        else:
            print(f"All keys in {file_name} are used.")

    return unused_keys


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

    find_unused_keys(default_values_yaml, templates_path, file_name="values.yaml")

    if args.additional_value_file:
        additional_paths = [os.path.join(chart_path, f) for f in args.additional_value_file]
        additional_values_yamls = load_additional_yaml_files(additional_paths)
        for file_path, values_dict in zip(additional_paths, additional_values_yamls):
            find_unused_keys(values_dict, templates_path, file_name=os.path.basename(file_path))

if __name__ == "__main__":
    main()
