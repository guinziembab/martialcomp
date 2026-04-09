#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build sw_translations.json from chunk dictionaries.
Run this script to generate the final translations file.
"""
import json
import os
import glob

def main():
    base_dir = os.path.dirname(__file__)
    all_translations = {}

    # Load all chunk files in order
    chunk_files = sorted(glob.glob(os.path.join(base_dir, 'sw_trans_chunk_*.py')))

    for chunk_file in chunk_files:
        print(f"Loading {os.path.basename(chunk_file)}...")
        chunk_dict = {}
        with open(chunk_file, 'r', encoding='utf-8') as f:
            code = f.read()
        exec(code, {'__builtins__': __builtins__}, chunk_dict)
        if 'TRANSLATIONS' in chunk_dict:
            all_translations.update(chunk_dict['TRANSLATIONS'])
            print(f"  Added {len(chunk_dict['TRANSLATIONS'])} entries (total: {len(all_translations)})")

    # Save final JSON
    output_path = os.path.join(base_dir, 'sw_translations.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_translations, f, ensure_ascii=False, indent=2)

    print(f"\nTotal translations: {len(all_translations)}")
    print(f"Saved to {output_path}")

if __name__ == '__main__':
    main()
