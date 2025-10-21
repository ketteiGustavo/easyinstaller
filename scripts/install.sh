#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Variables ---
readonly PROJECT_NAME="easyinstaller"
readonly BINARY_NAME="ei"
readonly GITHUB_REPO="ketteiGustavo/easyinstaller"
readonly INSTALL_DIR="/usr/local/bin"
readonly MAN_DIR="/usr/share/man/man1"
readonly DATA_DIR="/usr/local/share/easyinstaller"

# --- Functions ---

info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1" >&2
    exit 1
}

check_privileges() {
    if [ "$(id -u)" -ne 0 ]; then
        info "This script requires superuser privileges. Rerunning with sudo..."
        # Re-execute the script with sudo, passing all original arguments
        exec sudo "$0" "$@"
    fi
}

get_distro() {
    if [ -f /etc/os-release ]; then
        # freedesktop.org and systemd
        . /etc/os-release
        DISTRO=$ID
    else
        # Fallback for older systems
        DISTRO=$(uname -s)
    fi
    echo "$DISTRO"
}

# --- Main Script ---

main() {
    check_privileges

    info "Starting installation of $PROJECT_NAME..."

    local distro
    distro=$(get_distro)
    info "Detected distribution: $distro"

    # --- Download Assets ---
    info "Downloading assets from release $latest_version..."

    # Base URL for all assets
    local base_download_url="https://github.com/${GITHUB_REPO}/releases/download/${latest_version}"

    # Download binary
    local temp_binary=$(mktemp)
    local binary_url="${base_download_url}/ei-linux-glibc2.31-amd64" # Using glibc version as default
    info "Downloading binary from $binary_url..."
    if ! curl -L --progress-bar "$binary_url" -o "$temp_binary"; then
        error "Failed to download the binary. Please check the URL and your connection."
    fi

    # Download uninstall script
    local temp_uninstall=$(mktemp)
    local uninstall_url="${base_download_url}/uninstall.sh"
    info "Downloading uninstall script from $uninstall_url..."
    if ! curl -L --progress-bar "$uninstall_url" -o "$temp_uninstall"; then
        error "Failed to download the uninstall script."
    fi

    # Download man page
    local temp_manpage=$(mktemp)
    local manpage_url="${base_download_url}/ei.1"
    info "Downloading man page from $manpage_url..."
    if ! curl -L --progress-bar "$manpage_url" -o "$temp_manpage"; then
        error "Failed to download the man page."
    fi

    # Download license
    local temp_license=$(mktemp)
    local license_url="${base_download_url}/LICENSE"
    info "Downloading license from $license_url..."
    if ! curl -L --progress-bar "$license_url" -o "$temp_license"; then
        error "Failed to download the license file."
    fi

    # --- Installation ---
    info "Installing binary to $INSTALL_DIR/$BINARY_NAME..."
    install -m 755 "$temp_binary" "$INSTALL_DIR/$BINARY_NAME"
    rm "$temp_binary"

    info "Installing uninstall script to $DATA_DIR/uninstall.sh..."
    mkdir -p "$DATA_DIR"
    install -m 755 "$temp_uninstall" "$DATA_DIR/uninstall.sh"
    rm "$temp_uninstall"

    info "Installing license to $DATA_DIR/LICENSE..."
    install -m 644 "$temp_license" "$DATA_DIR/LICENSE"
    rm "$temp_license"

    info "Installing man page to $MAN_DIR/ei.1..."
    mkdir -p "$MAN_DIR"
    install -m 644 "$temp_manpage" "$MAN_DIR/ei.1"
    gzip -f "$MAN_DIR/ei.1"
    rm "$temp_manpage"

    info "Updating man-db..."
    if command -v mandb &> /dev/null; then
        mandb
    fi

    info "\033[1;32m✔ Installation successful!\033[0m"
    info "Run '$BINARY_NAME --help' to get started."
    info "To uninstall, run: sudo $DATA_DIR/uninstall.sh"
}

# Run the main function
main
