#!/usr/bin/env sh
# Convert all YAML under INPUT_DIR to PPTX under OUTPUT_DIR.
# Usage: docker compose run convert
# Input: files in mounted input/ (e.g. *.yaml, *.yml)
# Output: output/<stem>.pptx per input file

set -e
mkdir -p "${OUTPUT_DIR:?}"

converted=0
for f in "${INPUT_DIR}"/*.yaml "${INPUT_DIR}"/*.yml; do
  [ -f "$f" ] || continue
  base=$(basename "$f" .yaml)
  base="${base%.yml}"
  uv run process-to-pptx from-yaml "$f" -o "${OUTPUT_DIR}/${base}.pptx"
  converted=$((converted + 1))
done

if [ "$converted" -eq 0 ]; then
  echo "No .yaml/.yml files found in ${INPUT_DIR}. Put input files there and run again." 1>&2
  exit 1
fi
echo "Converted ${converted} file(s) to ${OUTPUT_DIR}"
