#!/bin/bash
set -e

python3 -m venv ${HELM_PLUGIN_DIR}/.venv
${HELM_PLUGIN_DIR}/.venv/bin/pip install --upgrade pip
${HELM_PLUGIN_DIR}/.venv/bin/pip install -r ${HELM_PLUGIN_DIR}/requirements.txt
