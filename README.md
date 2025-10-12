# 🧠 easy-installer (alias: `ei`)

**easy-installer** is a universal installation manager for Linux.

With a single command—`ei apt vscode`, `ei flatpak obsidian`, `ei snap telegram-desktop`—you can install applications from any source while keeping a **complete history** of all your actions.

Stop memorizing flags for different package managers. Just `ei`.

---

## 💡 Key Features

- **Unified Interface:** A single, consistent command for `apt`, `dnf`, `pacman`, `flatpak`, and `snap`.
- **Simple Installation:** Install any package with one command (e.g., `ei apt vscode`).
- **Automatic History:** Every installation is logged to `~/.local/share/easy-installer/history.jsonl`.
- **Portable Setup File:** Your entire setup is stored in a clean, human-readable file at `~/.config/easy-installer/setup.json`.
- **Replicate Your Environment:** Move to a new machine, run `ei import setup.json`, and have your environment back in minutes.
- **Idempotent:** The tool automatically detects what's already installed and skips it.
- **Alias-Free:** Installs a simple `ei` command for instant access, no shell configuration needed.

---

## ⚙️ Installation

You can install `easy-installer` with a single command. It will automatically detect your system architecture and download the latest pre-compiled binary.

```bash
curl -sSL https://raw.githubusercontent.com/your-username/easyinstaller/main/install.sh | bash
```
*(Note: The URL will be updated once the project is on GitHub).*

The script will install the `ei` binary to `/usr/local/bin`, making it available system-wide.

---

## 🚀 Usage Examples

```bash
# Install applications from different sources
ei add apt git
ei add flatpak obsidian
ei add snap telegram-desktop

# Apply a complete setup from a file
ei import setup.json

# Export your current setup
ei export

# View installation history
ei hist

# List all applications defined in your setup file
ei list
```

---

## 🧩 File Structure

`easy-installer` uses two simple files to manage your environment:

- `~/.config/easy-installer/setup.json`: Your portable setup definition. Edit it, share it, back it up.
- `~/.local/share/easy-installer/history.jsonl`: A detailed log of every installation and removal performed by `ei`.

These files are the key to **exporting** and **re-applying** your environment across different machines.

---

## 🛠️ Roadmap

- [x] Unified installer for native, Flatpak, and Snap packages.
- [x] Automatic installation history.
- [x] Portable `setup.json` for exporting and importing.
- [ ] **Removal Support:** `ei rm <package>` to uninstall any application.
- [ ] **Undo Command:** `ei undo` to revert the last operation.
- [ ] **Custom Aliases:** Define your own shortcuts in a configuration file.
- [ ] **System Update:** A unified command `ei update` to refresh all package sources.
- [ ] **Markdown Reports:** Generate a Markdown summary of your setup.

---

## 🧑‍💻 Author

**Luiz Gustavo**
💻 Linux user, Python developer, and environment automation enthusiast.
📦 This project was born from the need to simplify the lives of those who frequently format, reinstall, or manage multiple Linux systems.

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See the `LICENSE` file for details.