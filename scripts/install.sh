#!/usr/bin/env bash
set -euo pipefail

# --- Constantes ---
PROJECT_NAME="easyinstaller"
BINARY_BASENAME="ei"
GITHUB_REPO="ketteiGustavo/easyinstaller"

INSTALL_DIR="/usr/local/bin"
MAN_DIR="/usr/share/man/man1"
DATA_DIR="/usr/local/share/easyinstaller"

# --- Mensagens ---
info()  { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2; exit 1; }

prompt_language() {
  if [ -n "${EASYINSTALLER_LANG:-}" ]; then
    return
  fi

  printf "\nSelecione o idioma padrão do EasyInstaller:\n"
  printf "  1) English (United States) [en_US]\n"
  printf "  2) Português (Brasil) [pt_BR]\n"
  local choice=""
  if [ -t 0 ]; then
    read -r -p "Escolha [1]: " choice || choice=""
  elif [ -r /dev/tty ]; then
    read -r -p "Escolha [1]: " choice < /dev/tty || choice=""
  else
    choice=""
  fi
  case "${choice:-1}" in
    2|pt_BR|PT|pt|br|BR) EASYINSTALLER_LANG="pt_BR" ;;
    *) EASYINSTALLER_LANG="en_US" ;;
  esac

  export EASYINSTALLER_LANG
  printf "\n"
}

apply_language_preference() {
  local lang="${EASYINSTALLER_LANG:-}"
  [ -z "$lang" ] && return

  local ei_binary="${INSTALL_DIR}/${BINARY_BASENAME}"
  if [ ! -x "$ei_binary" ]; then
    warn "Não foi possível configurar o idioma automaticamente (binário não encontrado)."
    return
  fi

  local target_user="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"
  local cmd=( "$ei_binary" config set language "$lang" )

  if [ "$target_user" = "root" ]; then
    if EASYINSTALLER_LANG="$lang" "${cmd[@]}" >/dev/null 2>&1; then
      info "Idioma padrão configurado para ${lang}."
    else
      warn "Não foi possível definir o idioma preferido automaticamente."
    fi
  else
    if sudo -u "$target_user" EASYINSTALLER_LANG="$lang" "${cmd[@]}" >/dev/null 2>&1; then
      info "Idioma padrão configurado para ${lang} (usuário ${target_user})."
    else
      warn "Não foi possível definir o idioma preferido para o usuário ${target_user}."
    fi
  fi
}

# --- Privs ---
require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    info "This script requires superuser privileges. Rerunning with sudo..."
    exec sudo -E "$0" "$@"
  fi
}

# --- Descobertas do sistema ---
detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) echo "amd64" ;;
    aarch64|arm64) echo "arm64" ;;
    *) error "Arquitetura não suportada: $(uname -m)";;
  esac
}

detect_libc() {
  if ldd --version 2>&1 | grep -qi musl; then
    echo "musl"
  else
    echo "glibc"
  fi
}

latest_tag() {
  # Busca o header "location" do redirect para a última release.
  # É mais robusto que usar -w %{redirect_url} que pode falhar em alguns ambientes.
  local location_header
  location_header=$(curl -sLI "https://github.com/${GITHUB_REPO}/releases/latest" | grep -i "^location:")

  if [ -z "$location_header" ]; then
    error "Não consegui descobrir a última release (cabeçalho 'location' não encontrado)."
  fi

  # Extrai a tag da URL e remove quaisquer caracteres de controle (como \r).
  # Ex: location: .../tag/v0.1.0 -> v0.1.0
  local tag
  tag=$(echo "$location_header" | sed -n 's|.*/tag/\(v[0-9.]*\)|\1|p' | tr -d '[:cntrl:]')

  [ -n "${tag:-}" ] || error "Não consegui extrair a tag da URL: ${location_header}"
  echo "$tag"
}

# --- Download com fallback e verificação ---
dl() {
  # dl <url> <dest>
  curl -fL --retry 3 --retry-delay 2 --progress-bar "$1" -o "$2"
}

verify_sha256_if_exists() {
  # verify_sha256_if_exists <file> <url.sha256>
  local file="$1" sha_url="$2"
  local tmp_sha; tmp_sha="$(mktemp)"
  if curl -fsI "$sha_url" >/dev/null 2>&1; then
    info "Baixando checksum: $sha_url"
    dl "$sha_url" "$tmp_sha"
    if ! (cd "$(dirname "$file")" && sha256sum -c <(sed "s| .*|  $(basename "$file")|")) < "$tmp_sha"; then
      rm -f "$tmp_sha"
      error "Checksum SHA256 não confere para $(basename "$file")."
    fi
    rm -f "$tmp_sha"
  else
    warn "Checksum não encontrado; seguindo sem verificar."
  fi
}

cleanups=()
cleanup() { for f in "${cleanups[@]:-}"; do [ -e "$f" ] && rm -f "$f"; done; }
trap cleanup EXIT

main() {
  prompt_language
  require_root "$@"

  info "Instalando ${PROJECT_NAME}…"
  local ARCH LIBC TAG
  ARCH="$(detect_arch)"
  LIBC="$(detect_libc)"
  TAG="$(latest_tag)"

  info "Detectado: arch=${ARCH}, libc=${LIBC}, tag=${TAG}"

  # Decide qual binário
  local asset bin_url sha_url
  if [ "$LIBC" = "musl" ]; then
    asset="${BINARY_BASENAME}-linux-musl-${ARCH}"
  else
    # seu build atual só publica glibc2.31 para amd64; para arm64 ajuste quando habilitar
    if [ "$ARCH" != "amd64" ]; then
      warn "Artefato glibc arm64 ainda não publicado; tentando musl arm64."
      asset="${BINARY_BASENAME}-linux-musl-${ARCH}"
    else
      asset="${BINARY_BASENAME}-linux-glibc2.31-${ARCH}"
    fi
  fi

  local base="https://github.com/${GITHUB_REPO}/releases/download/${TAG}"
  bin_url="${base}/${asset}"
  sha_url="${bin_url}.sha256"

  # Baixa binário
  local tmp_bin; tmp_bin="$(mktemp)"; cleanups+=("$tmp_bin")
  info "Baixando binário: $bin_url"
  dl "$bin_url" "$tmp_bin" || error "Não consegui baixar o binário ${asset}."
  chmod +x "$tmp_bin"

  # Verifica SHA256 se existir
  verify_sha256_if_exists "$tmp_bin" "$sha_url"

  # Arquivos opcionais
  mkdir -p "$DATA_DIR" "$MAN_DIR"

  for name in uninstall.sh ei.1 LICENSE; do
    src_url="${base}/${name}"
    tmp="$(mktemp)"; cleanups+=("$tmp")
    if curl -fsI "$src_url" >/dev/null 2>&1; then
      info "Baixando $name"
      dl "$src_url" "$tmp"
      case "$name" in
        uninstall.sh) install -m 755 "$tmp" "$DATA_DIR/uninstall.sh" ;;
        ei.1)         install -m 644 "$tmp" "$MAN_DIR/ei.1" && gzip -f "$MAN_DIR/ei.1" ;;
        LICENSE)      install -m 644 "$tmp" "$DATA_DIR/LICENSE" ;;
      esac
    else
      warn "$name não anexado na release (ok, seguindo)."
    fi
  done

  # Instala binário
  install -m 755 "$tmp_bin" "${INSTALL_DIR}/${BINARY_BASENAME}"

  # Atualiza base de man se existir
  if command -v mandb >/dev/null 2>&1; then
    info "Atualizando man-db…"
    mandb >/dev/null 2>&1 || true
  fi

  apply_language_preference

  info "✔ Instalação concluída! Execute: ${BINARY_BASENAME} --help"
  info "Desinstalar: sudo ${DATA_DIR}/uninstall.sh (se baixado)"
}

main "$@"
