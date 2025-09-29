import os
import sys
import subprocess

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TRANSLATIONS_DIR = os.path.join(PROJECT_ROOT, "translations")
LANGUAGES = ["fa", "ru", "ar", "zh"]  # "ar" is already here, which is good.
SOURCE_FILES = [
    "main.py",
    "constants.py",
    "settings_manager.py",
    "managers/server_manager.py",
    "link_parser.py",
    "ui/main_window.py",
    "ui/app_logic.py",
    "ui/dialogs/about.py",
    "ui/dialogs/server_edit.py",
    "ui/dialogs/subscription.py",
    "ui/views/connection_view.py",
    "ui/views/settings_view.py",
]
TS_FILE_PREFIX = "onix"


def find_executable(name):
    """Finds an executable in the Python scripts directory."""
    if sys.platform == "win32":
        exe_name = f"{name}.exe"
        scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
    else:
        exe_name = name
        scripts_dir = os.path.join(os.path.dirname(sys.executable), "bin")

    path = os.path.join(scripts_dir, exe_name)
    if os.path.exists(path):
        return path
    # Fallback to PATH if not in venv scripts dir
    return name


def run_command(command):
    """Runs a command and checks for errors."""
    print(f"Executing: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True,
                            text=True, encoding='utf-8')
    if result.returncode != 0:
        print(f"--- ERROR ---")
        print(result.stdout)
        print(result.stderr)
        print(f"-------------")
        return False
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return True


def main():
    """Main function to update and compile translations."""
    lupdate_exe = find_executable("pyside6-lupdate")
    lrelease_exe = find_executable("pyside6-lrelease")

    print("--- 1. Updating translation source files (.ts) ---")
    ts_files = [os.path.join(
        TRANSLATIONS_DIR, f"{TS_FILE_PREFIX}_{lang}.ts") for lang in LANGUAGES]
    source_paths = [os.path.join(PROJECT_ROOT, f) for f in SOURCE_FILES]

    lupdate_cmd = [lupdate_exe, "-no-obsolete"] + \
        source_paths + ["-ts"] + ts_files
    if not run_command(lupdate_cmd):
        print("\nFailed to update .ts files. Aborting.")
        sys.exit(1)

    print("\n--- 2. Compiling translation files (.qm) ---")
    for ts_file in ts_files:
        if not os.path.exists(ts_file):
            print(f"Warning: {ts_file} not found. Skipping.")
            continue
        lrelease_cmd = [lrelease_exe, ts_file]
        run_command(lrelease_cmd)

    print("\n--- Translation update complete. ---")


if __name__ == "__main__":
    main()
