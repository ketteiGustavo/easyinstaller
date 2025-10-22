# 🧠 easy-installer (alias: `ei`)

**easy-installer** is a universal installation manager for Linux.

With a single command—`ei add vscode`—you can search and install applications from multiple sources (`apt`, `flatpak`, `snap`) while keeping a **complete history** of all your actions.

Stop memorizing commands and flags for different package managers. Just `ei`.

---

## 💡 Key Features

- **Unified Search & Install:** The `ei add` command searches Apt, Flathub, and Snap simultaneously, presenting a clear menu for you to choose the best option.
- **Consistent Interface:** A single command for the most common operations, such as `add`, `rm`, `list`, and `hist`.
- **Legacy Commands:** Still prefer to use a specific manager? `ei apt ...`, `ei flatpak ...`, and `ei snap ...` work as you'd expect.
- **Automatic History:** Every installation and removal is logged to `~/.local/share/easyinstaller/history.jsonl`.
- **Export & Import Your Environment:** Save your package setup with `ei export` and replicate it on a new machine with `ei import`.
- **Idempotent:** The tool detects what is already installed and skips reinstallation.

---

## ⚙️ Installation

You can install `easy-installer` with a single command. It will automatically detect your system's architecture and download the latest pre-compiled binary.

The script will request superuser privileges (`sudo`) to install `ei` to `/usr/local/bin`.

```bash
curl -fsSL https://raw.githubusercontent.com/ketteiGustavo/easyinstaller/main/scripts/install.sh | sudo bash
```

---

## 🚀 Commands

| Command | Description |
| :--- | :--- |
| `ei add <pkg...>` | Searches for and installs packages from Apt, Flathub, and Snap. |
| `ei rm <pkg...>` | Removes one or more installed packages. |
| `ei list [mgr...]` | Lists all installed packages, with an optional filter by manager. |
| `ei hist` | Displays the history of installations and removals. |
| `ei export` | Exports your installed package configuration to a JSON file. |
| `ei import <file>` | Installs packages from an exported JSON file. |
| `ei update` | Checks for and installs updates for `easyinstaller`. |
| `ei uninstall` | Removes `easyinstaller` from your system. |
| `ei license` | Displays the software license. |
| `ei completion` | Generates shell completion scripts. |

---

## 🧩 File Structure

`easy-installer` uses a simple, standard file structure to manage your environment:

- `~/.config/easyinstaller/config.json`: Main configuration file (language, default paths).
- `~/.local/share/easyinstaller/history.jsonl`: A detailed log of every operation performed.
- `~/.local/share/easyinstaller/exports/`: The default directory for exported setup files.

---

## 🛠️ Roadmap

- [x] Unified installer (`ei add`).
- [x] Automatic installation history (`ei hist`).
- [x] Portable setup file (`ei export`/`import`).
- [x] Removal support (`ei rm`).
- [x] Self-update mechanism (`ei update`).
- [ ] **Undo Command:** `ei undo` to revert the last operation.
- [ ] **System Update:** A unified `ei sys-update` command to refresh all package sources (`apt update`, etc.).
- [ ] **Markdown Reports:** Generate a summary of your setup in Markdown format.

---

## 🧑‍💻 Author

**Luiz Gustavo**

💻 Linux user, Python developer, and environment automation enthusiast.
📦 This project was born from the need to simplify the lives of those who frequently format, reinstall, or manage multiple Linux systems.

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See the `LICENSE` file for details.
