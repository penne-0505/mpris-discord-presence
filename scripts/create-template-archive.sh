#!/usr/bin/env bash
set -euo pipefail

output="${1:-docs_driven_dev_template.zip}"
git archive --format=zip --output="$output" HEAD
echo "Created $output"
