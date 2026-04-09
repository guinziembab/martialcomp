#!/usr/bin/env python3
"""Make the drag & drop panels sticky with fixed viewport height."""

filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html"

with open(filepath, "r") as f:
    content = f.read()

# 1. Fix the main container - make it position sticky
old_container = '<div class="row" id="dragDropInterface" style="height: calc(100vh - 280px); min-height: 450px;">'
new_container = '<div class="row" id="dragDropInterface" style="position: sticky; top: 0; height: 100vh; min-height: 450px; z-index: 10;">'
content = content.replace(old_container, new_container)

# 2. Add/update CSS to make both panels properly contained
css_fix = """
    /* Fixed panels for drag & drop */
    #dragDropInterface {
        position: sticky !important;
        top: 0 !important;
        height: 100vh !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    #dragDropInterface > .col-md-4,
    #dragDropInterface > .col-md-8 {
        height: 100%;
        max-height: 100vh;
    }
    #dragDropInterface > .col-md-4 > .card,
    #dragDropInterface > .col-md-8 > .card {
        max-height: calc(100vh - 20px);
        display: flex;
        flex-direction: column;
    }
    #dragDropInterface .practitioner-list-container {
        flex: 1 1 0;
        overflow-y: auto !important;
        min-height: 0;
    }
    #dragDropInterface > .col-md-8 > .card > .card-body {
        flex: 1 1 0;
        overflow-y: auto !important;
        min-height: 0;
    }
    /* Scrollbar styling */
    #dragDropInterface .practitioner-list-container::-webkit-scrollbar,
    #dragDropInterface > .col-md-8 > .card > .card-body::-webkit-scrollbar {
        width: 6px;
    }
    #dragDropInterface .practitioner-list-container::-webkit-scrollbar-track,
    #dragDropInterface > .col-md-8 > .card > .card-body::-webkit-scrollbar-track {
        background: transparent;
    }
    #dragDropInterface .practitioner-list-container::-webkit-scrollbar-thumb,
    #dragDropInterface > .col-md-8 > .card > .card-body::-webkit-scrollbar-thumb {
        background: rgba(201, 162, 39, 0.4);
        border-radius: 3px;
    }
"""

# Insert before first </style>
style_end = content.find("</style>")
if style_end != -1:
    content = content[:style_end] + css_fix + "\n" + content[style_end:]
    print("CSS fixed")

with open(filepath, "w") as f:
    f.write(content)
print("DONE")
