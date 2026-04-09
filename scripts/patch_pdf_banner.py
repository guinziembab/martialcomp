#!/usr/bin/env python3
"""Add banner image to PDF export header."""

filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/pdf_export.py"
with open(filepath, "r") as f:
    content = f.read()

# Replace the _draw_header function to include banner
old_header = '''def _draw_header(c, competition, page_width, page_height):
    """Draw competition header on each page."""
    # Dark header bar
    c.setFillColor(DARK_BG)
    c.rect(0, page_height - 35*mm, page_width, 35*mm, fill=1, stroke=0)

    # Gold accent line
    c.setFillColor(GOLD)
    c.rect(0, page_height - 36*mm, page_width, 1.5*mm, fill=1, stroke=0)

    # Competition name
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(15*mm, page_height - 15*mm, competition.title or "Competition")

    # Date and location
    c.setFillColor(TEXT_WHITE)
    c.setFont("Helvetica", 9)
    info_parts = []
    if competition.start_date:
        info_parts.append(competition.start_date.strftime("%d/%m/%Y"))
    if competition.venue_name:
        info_parts.append(competition.venue_name)
    if hasattr(competition, 'discipline') and competition.discipline:
        info_parts.append(str(competition.discipline))
    c.drawString(15*mm, page_height - 23*mm, " | ".join(info_parts))

    # Stats
    reg_count = CompetitionRegistration.objects.filter(competition=competition).count()
    cat_count = CompetitionCategory.objects.filter(competition=competition).count()
    type_count = competition.competition_types.count()
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_MUTED)
    stats = f"{reg_count} pratiquants | {cat_count} categories | {type_count} types"
    c.drawString(15*mm, page_height - 30*mm, stats)

    return page_height - 40*mm  # Return Y position below header'''

new_header = '''def _draw_header(c, competition, page_width, page_height, is_first_page=False):
    """Draw competition header on each page, with banner on first page."""
    import os
    from django.conf import settings
    from reportlab.lib.utils import ImageReader

    banner_height = 0

    # Banner image on first page
    if is_first_page and competition.logo:
        try:
            img_path = os.path.join(settings.MEDIA_ROOT, str(competition.logo))
            if os.path.exists(img_path):
                img = ImageReader(img_path)
                iw, ih = img.getSize()
                aspect = ih / iw
                banner_w = page_width - 20*mm
                banner_h = banner_w * aspect
                # Cap banner height
                if banner_h > 60*mm:
                    banner_h = 60*mm
                    banner_w = banner_h / aspect
                banner_x = (page_width - banner_w) / 2
                banner_y = page_height - 10*mm - banner_h
                # Dark background behind banner
                c.setFillColor(DARK_BG)
                c.rect(0, banner_y - 3*mm, page_width, banner_h + 16*mm, fill=1, stroke=0)
                c.drawImage(img_path, banner_x, banner_y, width=banner_w, height=banner_h, preserveAspectRatio=True, mask='auto')
                banner_height = banner_h + 16*mm
        except Exception:
            pass

    # Dark header bar (below banner or at top)
    header_top = page_height - banner_height
    c.setFillColor(DARK_BG)
    c.rect(0, header_top - 28*mm, page_width, 28*mm, fill=1, stroke=0)

    # Gold accent line
    c.setFillColor(GOLD)
    c.rect(0, header_top - 29*mm, page_width, 1.5*mm, fill=1, stroke=0)

    # Competition name
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 14)
    title = competition.title or "Competition"
    if len(title) > 60:
        title = title[:57] + "..."
    c.drawString(15*mm, header_top - 12*mm, title)

    # Date and location
    c.setFillColor(TEXT_WHITE)
    c.setFont("Helvetica", 9)
    info_parts = []
    if competition.start_date:
        info_parts.append(competition.start_date.strftime("%d/%m/%Y"))
    if competition.venue_name:
        info_parts.append(competition.venue_name)
    if hasattr(competition, 'discipline') and competition.discipline:
        info_parts.append(str(competition.discipline))
    c.drawString(15*mm, header_top - 20*mm, " | ".join(info_parts))

    # Stats
    reg_count = CompetitionRegistration.objects.filter(competition=competition).count()
    cat_count = CompetitionCategory.objects.filter(competition=competition).count()
    type_count = competition.competition_types.count()
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_MUTED)
    stats = f"{reg_count} pratiquants | {cat_count} categories | {type_count} types"
    c.drawString(15*mm, header_top - 26*mm, stats)

    return header_top - 32*mm  # Return Y position below header'''

if old_header in content:
    content = content.replace(old_header, new_header)
    print("Header function replaced")
else:
    print("ERROR: old header not found")

# Update the first call to _draw_header to pass is_first_page=True
# Find the first call pattern
old_first_call = "        if page_num > 0:\n            c.showPage()\n        page_num += 1\n\n        y = _draw_header(c, competition, page_width, page_height)"
new_first_call = "        if page_num > 0:\n            c.showPage()\n        page_num += 1\n\n        y = _draw_header(c, competition, page_width, page_height, is_first_page=(page_num == 1))"

if old_first_call in content:
    content = content.replace(old_first_call, new_first_call, 1)
    print("First call updated with is_first_page")
else:
    print("WARNING: first call pattern not found")

with open(filepath, "w") as f:
    f.write(content)

print("DONE")
