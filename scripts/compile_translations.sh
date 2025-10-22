#!/usr/bin/env bash
set -euo pipefail

# Compile all gettext catalogs used by EasyInstaller.
# Usage: scripts/compile_translations.sh

if ! command -v msgfmt >/dev/null 2>&1; then
  echo "Error: msgfmt (gettext) is not installed." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCALE_DIR="${REPO_ROOT}/src/easyinstaller/locales"

LOCALES=(
  "en_US"
  "pt_BR"
)

for locale in "${LOCALES[@]}"; do
  po_file="${LOCALE_DIR}/${locale}/LC_MESSAGES/easyinstaller.po"
  mo_file="${LOCALE_DIR}/${locale}/LC_MESSAGES/easyinstaller.mo"

  if [[ ! -f "${po_file}" ]]; then
    echo "Warning: PO file not found for locale '${locale}': ${po_file}" >&2
    continue
  fi

  mkdir -p "$(dirname "${mo_file}")"
  echo "Compiling ${po_file} -> ${mo_file}"
  msgfmt "${po_file}" -o "${mo_file}"
done

echo "Translation catalogs compiled successfully."
