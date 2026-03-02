"""Fix all entity files to work with updated BaseEntity."""
import os
import re

MODULES_DIR = r"E:\PROGECTS\kontrolling\backend\app\modules"

# Find all entities.py files
for root, dirs, files in os.walk(MODULES_DIR):
    if "entities.py" in files:
        filepath = os.path.join(root, "entities.py")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add field import if not present
        if "from dataclasses import dataclass" in content and "field" not in content:
            content = content.replace(
                "from dataclasses import dataclass",
                "from dataclasses import dataclass, field"
            )
        
        # Find entity classes that inherit from BaseEntity and have required fields after id
        # We need to reorder fields or add defaults
        if "@dataclass\nclass" in content:
            # Skip if already fixed
            if "BaseEntity" not in content:
                continue
            
            # Write back
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Checked: {os.path.relpath(filepath, MODULES_DIR)}")

print("Done!")
