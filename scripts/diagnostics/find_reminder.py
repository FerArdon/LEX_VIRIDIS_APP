
filename = r"F:\LEX_VIRIDIS_APP\lexviridis\ui_v2.py"
search_term = "_show_reminder_dialog"

try:
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if search_term in line:
                print(f"Found at line {i+1}: {line.strip()}")
except Exception as e:
    print(f"Error: {e}")
