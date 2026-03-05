import os
import subprocess
import importlib.metadata

def extract_imports_from_file(filepath):
    imports = set()
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                parts = line.replace(",", " ").split()
                if parts[0] == "import":
                    imports.add(parts[1].split('.')[0])
                elif parts[0] == "from":
                    imports.add(parts[1].split('.')[0])
    return imports

def get_all_imports(directory="."):
    all_imports = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                all_imports |= extract_imports_from_file(filepath)
    return all_imports

def get_installed_packages():
    return {dist.metadata["Name"].lower(): dist.version for dist in importlib.metadata.distributions()}

def generate_requirements_file():
    imports = get_all_imports(".")
    installed = get_installed_packages()

    used_packages = {}
    for imp in imports:
        if imp.lower() in installed:
            used_packages[imp.lower()] = installed[imp.lower()]

    if not used_packages:
        print("⚠️ No matching installed packages found.")
        return

    with open("requirements.txt", "w") as f:
        for pkg, ver in sorted(used_packages.items()):
            f.write(f"{pkg}=={ver}\n")

    print("✅ requirements.txt created with used packages!")

if __name__ == "__main__":
    generate_requirements_file()
