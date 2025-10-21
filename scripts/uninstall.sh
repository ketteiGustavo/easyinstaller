#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Variables ---
readonly PROJECT_NAME="easyinstaller"
readonly BINARY_NAME="ei"
readonly INSTALL_DIR="/usr/local/bin"
readonly MAN_DIR="/usr/share/man/man1"
readonly DATA_DIR="/usr/local/share/easyinstaller"

# --- Functions ---

info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

check_privileges() {
    if [ "$(id -u)" -ne 0 ]; then
        info "This script requires superuser privileges. Please run with sudo."
        exit 1
    fi
}

# --- Main Script ---

main() {
    check_privileges

    info "Uninstalling $PROJECT_NAME..."

    info "Removing binary from $INSTALL_DIR..."
    rm -f "$INSTALL_DIR/$BINARY_NAME"

    # This assumes the man page was installed and gzipped, which is standard.
    info "Removing man page..."
    rm -f "$MAN_DIR/ei.1.gz"

    info "Updating man-db..."
    # Run mandb if it exists to clean up the database.
    if command -v mandb &> /dev/null; then
        mandb
    fi

    info "Removing data directory $DATA_DIR..."
    # This will remove the uninstall script itself.
    rm -rf "$DATA_DIR"

    info "\033[1;32m✔ $PROJECT_NAME has been successfully uninstalled.\033[0m"
}

# Run the main function
main
