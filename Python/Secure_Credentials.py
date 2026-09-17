from pathlib import Path
import re

PYTHON_FOLDER = Path(__file__).resolve().parent

updated_files = []

password_pattern = re.compile(
    r'MYSQL_PASSWORD\s*=\s*["\'][^"\']*["\']'
)

replacement = (
    'MYSQL_PASSWORD = getpass("Enter MySQL password: ")'
)

for file_path in PYTHON_FOLDER.glob("*.py"):

    # Indha security script-ai modify panna vendam.
    if file_path.name == "Secure_Credentials.py":
        continue

    original_text = file_path.read_text(
        encoding="utf-8"
    )

    # Hardcoded password irundha mattum replace pannum.
    updated_text, replacement_count = (
        password_pattern.subn(
            replacement,
            original_text,
        )
    )

    if replacement_count == 0:
        continue

    # getpass import illa na add pannum.
    if (
        "from getpass import getpass"
        not in updated_text
    ):
        updated_text = (
            "from getpass import getpass\n"
            + updated_text
        )

    file_path.write_text(
        updated_text,
        encoding="utf-8",
    )

    updated_files.append(file_path.name)

print("=" * 72)
print("CREDENTIAL SECURITY UPDATE COMPLETED")
print("=" * 72)

if updated_files:
    print("\nUpdated files:")

    for file_name in updated_files:
        print(f" - {file_name}")
else:
    print("\nNo hardcoded MySQL passwords found.")

print(
    "\nAll updated scripts will now ask for "
    "the MySQL password securely."
)