#!/usr/bin/env python3

import os
import shutil

SRC_DIR = "/home/lorenzo/repos/pdfextractor2/solution/src/pdfextractor"

print("🧹 Cleaning and reorganizing PDF Extractor project...")

print("\n1. Removing old config.py (replaced by settings.py)...")
config_path = os.path.join(SRC_DIR, "config.py")
if os.path.exists(config_path):
    os.remove(config_path)
    print("   ✓ Removed config.py")

print("\n2. Removing empty extraction directory...")
extraction_dir = os.path.join(SRC_DIR, "extraction")
if os.path.exists(extraction_dir) and not os.listdir(extraction_dir):
    shutil.rmtree(extraction_dir)
    print("   ✓ Removed empty extraction directory")

print("\n3. Removing __pycache__ directories...")
for root, dirs, files in os.walk(SRC_DIR):
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        shutil.rmtree(pycache_path)
        print(f"   ✓ Removed {pycache_path}")

print("\n✅ Cleanup complete!")
print("\nRemaining files:")
for root, dirs, files in os.walk(SRC_DIR):
    level = root.replace(SRC_DIR, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        if file.endswith('.py'):
            print(f'{subindent}{file}')
