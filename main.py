import os
import yaml
import re
import argparse
import sys
from collections import defaultdict

def load_chart_yaml(chart_path):
    """
    Load and parse the Chart.yaml from the given chart path.
    Returns the parsed YAML as a dictionary.
    """
    try:
        with open(os.path.join(chart_path, 'Chart.yaml'), 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"{e}")
        sys.exit(2)

def verify_chart_dependencies(chart_file):
    """
    Look for dependencies in the Chart.yaml.
    Returns a list of the repository URLs.
    """
    if 'dependencies' not in chart_file or not chart_file['dependencies']:
        print("No dependencies found in Chart.yaml.")
        return []

    print("Chart dependencies:")
    chart_dependencies = []
    for dependency in chart_file['dependencies']:
        repo = dependency.get('repository')
        # RegEx for extracting the repository name from the URL
        repository_name = re.search(r'/([^/]+)/?$', repo).group(1)
        chart_dependencies.append(repository_name)

    return chart_dependencies





def load_values_yaml(values_file):
    try:
        with open(values_file, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"{e}")
        sys.exit(2)

def merge_dicts(base, updates, source_map, source_file, prefix=""):
    """
    Recursively merge two dictionaries. Values from `updates` overwrite `base`.
    Tracks the source of each key in `source_map`.
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
    try:
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
    except Exception as e:
        print(f"{e}")
        sys.exit(2)

    unused_keys = [key for key in flattened_keys if key not in used_keys]

    unused_keys_with_sources = [(key, source_map.get(key, "unknown source")) for key in unused_keys]

    return unused_keys_with_sources

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

    # chart_path = os.path.abspath(args.chart)
    chart_file = load_chart_yaml(args.chart)
    chart_dependencies = verify_chart_dependencies(chart_file)
    print(chart_dependencies)




    # # Alle Templates und values.yaml-Dateien finden
    # templates_dirs, values_files = find_all_templates_and_values(chart_path)

    # # Hauptwerte laden
    # values = {}
    # source_map = {}
    # for values_file in values_files:
    #     if os.path.exists(values_file):
    #         additional_values = load_values_yaml(values_file)
    #         merge_dicts(values, additional_values, source_map, values_file)

    # # Zusätzliche Werte-Dateien laden
    # if args.additional_value_file:
    #     for additional_file in args.additional_value_file:
    #         additional_file_path = os.path.join(chart_path, additional_file)
    #         if os.path.exists(additional_file_path):
    #             additional_values = load_values_yaml(additional_file_path)
    #             merge_dicts(values, additional_values, source_map, additional_file_path)

    # # Unbenutzte Schlüssel finden
    # unused_keys_with_sources = []
    # for templates_dir in templates_dirs:
    #     if os.path.exists(templates_dir):
    #         unused_keys_with_sources.extend(find_unused_keys(values, templates_dir, source_map))

    # # Ergebnisse ausgeben
    # if unused_keys_with_sources:
    #     # Group unused keys by their source file
    #     grouped_unused_keys = defaultdict(list)
    #     for key, source in unused_keys_with_sources:
    #         grouped_unused_keys[source].append(key)

    #     for source, keys in grouped_unused_keys.items():
    #         print(f"Unused keys in {source}:")
    #         for key in keys:
    #             print(f"  - {key}")
    # else:
    #     print("All keys in values files are used in the templates.")

if __name__ == "__main__":
    main()
