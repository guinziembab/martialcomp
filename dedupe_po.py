#!/usr/bin/env python3
"""Remove duplicate msgid entries from PO files, keeping the best translation."""
import re
import os

LOCALES = ['en','de','es','it','pt','ar','hi','ja','ko','no','ru','sw','vi','yo','zh','zu','am']

for loc in LOCALES:
    po_path = f'locale/{loc}/LC_MESSAGES/django.po'
    if not os.path.exists(po_path):
        continue

    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse into blocks: each block is a msgid/msgstr pair with optional comments
    blocks = []
    current_block = []

    for line in lines:
        if line.startswith('#') and current_block and any(l.startswith('msgid ') for l in current_block):
            # Start of new block
            blocks.append(current_block)
            current_block = [line]
        elif line.startswith('msgid ') and current_block and any(l.startswith('msgid ') for l in current_block):
            # New msgid without comment prefix
            blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    # Now deduplicate
    seen = {}  # msgid -> index in kept list
    kept = []
    dupes = 0

    for block in blocks:
        # Extract msgid from this block
        msgid = None
        msgstr = None
        for line in block:
            if line.startswith('msgid "'):
                msgid = line[7:-2]  # strip msgid " and "\n
            if line.startswith('msgstr "'):
                msgstr = line[8:-2]  # strip msgstr " and "\n

        if msgid is None or msgid == '':
            # Header or empty - always keep
            kept.append(block)
            continue

        if msgid in seen:
            dupes += 1
            # Check if new block has better translation
            idx = seen[msgid]
            old_block = kept[idx]
            old_msgstr = None
            for line in old_block:
                if line.startswith('msgstr "'):
                    old_msgstr = line[8:-2]

            # Keep the one with non-empty, non-broken translation
            if msgstr and (not old_msgstr or '?' in old_msgstr):
                kept[idx] = block
        else:
            seen[msgid] = len(kept)
            kept.append(block)

    # Write back
    with open(po_path, 'w', encoding='utf-8') as f:
        for block in kept:
            f.writelines(block)

    if dupes > 0:
        print(f'{loc}: removed {dupes} duplicates')
    else:
        print(f'{loc}: clean')

print('Done!')
