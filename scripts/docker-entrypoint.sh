#!/usr/bin/env sh
# Convert all YAML under SRC_DIR to PPTX under GEN_DIR.
# Usage: docker compose run build
# Input: files in mounted src/ (e.g. *.yaml, *.yml)
# Output: gen/<stem>.pptx per input file

set -e
mkdir -p "${GEN_DIR:?}"

converted=0
for f in "${SRC_DIR}"/*.yaml "${SRC_DIR}"/*.yml; do
  [ -f "$f" ] || continue
  base=$(basename "$f" .yaml)
  base="${base%.yml}"
  uv run process-to-pptx from-yaml "$f" -o "${GEN_DIR}/${base}.pptx"
  converted=$((converted + 1))
done

if [ "$converted" -eq 0 ]; then
  echo "No .yaml/.yml files found in ${SRC_DIR}. Put input files there and run again." 1>&2
  exit 1
fi
echo "Converted ${converted} file(s) to ${GEN_DIR}"
