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

    # TODO: Replace this with actual release version detection
    local latest_version="v0.1.0"

    # Placeholder for binary name based on distro. 
    # This will be defined in the GitHub release workflow.
    local compiled_binary_name="${BINARY_NAME}-${distro}-amd64"
    local download_url="https://github.com/${GITHUB_REPO}/releases/download/${latest_version}/${compiled_binary_name}"

    info "Downloading from $download_url..."
    local temp_binary
    temp_binary=$(mktemp)

    if ! curl -L --progress-bar "$download_url" -o "$temp_binary"; then
        error "Failed to download the binary. Please check the URL and your connection."
    fi

    info "Installing binary to $INSTALL_DIR/$BINARY_NAME..."
    install -m 755 "$temp_binary" "$INSTALL_DIR/$BINARY_NAME"
    rm "$temp_binary"

    # --- Create Uninstall Script ---
    info "Creating uninstall script at $DATA_DIR/uninstall.sh..."
    mkdir -p "$DATA_DIR"

    # Use a heredoc to write the uninstall script
    cat <<EOF > "$DATA_DIR/uninstall.sh"
#!/bin/bash

echo "Uninstalling $PROJECT_NAME..."

# Stop on error
set -e

if [ "\$(id -u)" -ne 0 ]; then
    echo "Uninstall script requires superuser privileges. Please run with sudo."
    exit 1
fi

echo "Removing binary..."
rm -f "$INSTALL_DIR/$BINARY_NAME"

# TODO: Uncomment when man page is ready
# echo "Removing man page..."
# rm -f "$MAN_DIR/ei.1.gz"
# mandb

echo "Removing data directory..."
rm -rf "$DATA_DIR"

echo "$PROJECT_NAME has been successfully uninstalled."

EOF

    chmod +x "$DATA_DIR/uninstall.sh"

    info "\033[1;32m✔ Installation successful!\033[0m"
    info "Run '$BINARY_NAME --help' to get started."
    info "To uninstall, run: sudo $DATA_DIR/uninstall.sh"
}

# Run the main function
main
