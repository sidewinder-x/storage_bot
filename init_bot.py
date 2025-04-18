import os

folders = [
    "handlers",
    "keyboards",
    "states",
    "utils"
]

files = {
    "bot.py": "",
    "config.py": "",
    "database.py": "",
    "handlers/__init__.py": "",
    "handlers/main_menu.py": "",
    "handlers/products.py": "",
    "handlers/finance.py": "",
    "handlers/family.py": "",
    "handlers/settings.py": "",
    "keyboards/__init__.py": "",
    "keyboards/menu.py": "",
    "keyboards/product_kb.py": "",
    "keyboards/finance_kb.py": "",
    "states/__init__.py": "",
    "states/product_states.py": "",
    "states/finance_states.py": "",
    "utils/__init__.py": "",
    "utils/helpers.py": ""
}

def create_project():
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    for file, content in files.items():
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)
    print("✅ Проект успешно создан!")

if __name__ == "__main__":
    create_project()