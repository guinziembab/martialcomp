#!/usr/bin/env python3
"""Add filterByType JS function definition."""

path = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/liste_equipes_par_categorie.html"
with open(path) as f:
    content = f.read()

if "function filterByType" not in content:
    last_script_end = content.rfind("</script>")
    if last_script_end != -1:
        js = (
            "\n"
            "    function filterByType(typeId, btn) {\n"
            "        document.querySelectorAll('.type-filter-btn').forEach(function(b) {\n"
            "            b.classList.remove('active');\n"
            "            b.classList.remove('btn-primary');\n"
            "            b.classList.add('btn-outline-primary');\n"
            "        });\n"
            "        btn.classList.add('active');\n"
            "        btn.classList.remove('btn-outline-primary');\n"
            "        btn.classList.add('btn-primary');\n"
            "        document.querySelectorAll('.category-section[data-type-id]').forEach(function(section) {\n"
            "            if (typeId === 'all' || section.dataset.typeId === String(typeId)) {\n"
            "                section.style.display = '';\n"
            "            } else {\n"
            "                section.style.display = 'none';\n"
            "            }\n"
            "        });\n"
            "    }\n"
        )
        content = content[:last_script_end] + js + content[last_script_end:]
        with open(path, 'w') as f:
            f.write(content)
        print("DONE")
    else:
        print("No script tag")
else:
    print("Already exists")
