
with open(r"C:\Users\frard\OneDrive\LEX_VIRIDIS_APP\lexviridis\ui_v2.py", encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "ft.Alignment." in line:
            print(f"{i+1}: {line.strip()}")
