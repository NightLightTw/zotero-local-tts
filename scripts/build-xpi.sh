#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_dir="$project_dir/zotero-plugin"
output_dir="$project_dir/dist"
version=$(plutil -extract version raw -o - "$source_dir/manifest.json")
output="$output_dir/zotero-local-tts-$version.xpi"
stage=$(mktemp -d "${TMPDIR:-/tmp}/zotero-local-tts.XXXXXX")
trap 'rm -rf "$stage"' EXIT HUP INT TERM

mkdir -p "$output_dir"
rm -f "$output"
cp "$source_dir/manifest.json" "$source_dir/bootstrap.js" "$stage/"
cp "$project_dir/LICENSE" "$project_dir/NOTICE" "$stage/"
(
  cd "$stage"
  zip -X -q -r "$output" manifest.json bootstrap.js LICENSE NOTICE
)
echo "$output"
