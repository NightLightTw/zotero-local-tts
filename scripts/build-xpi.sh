#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir="$project_dir/zotero-plugin"
output_dir="$project_dir/dist"
output="$output_dir/zotero-local-tts-0.1.2.xpi"

mkdir -p "$output_dir"
rm -f "$output"
(
  cd "$source_dir"
  zip -X -q -r "$output" manifest.json bootstrap.js
)
echo "$output"
