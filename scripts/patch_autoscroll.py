#!/usr/bin/env python3
"""Add auto-scroll during drag & drop and click-to-assign mode."""

filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html"

with open(filepath, "r") as f:
    content = f.read()

# 1. Add CSS for click-to-assign mode
css_addition = """
    /* Auto-scroll indicators */
    .scroll-indicator-top, .scroll-indicator-bottom {
        position: absolute;
        left: 0;
        right: 0;
        height: 40px;
        z-index: 10;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s;
    }
    .scroll-indicator-top {
        top: 0;
        background: linear-gradient(to bottom, rgba(201,162,39,0.3), transparent);
    }
    .scroll-indicator-bottom {
        bottom: 0;
        background: linear-gradient(to top, rgba(201,162,39,0.3), transparent);
    }
    .scroll-indicator-top.active, .scroll-indicator-bottom.active {
        opacity: 1;
    }

    /* Click-to-assign mode */
    .practitioner-drag-item.selected-for-assign {
        background: rgba(201, 162, 39, 0.3) !important;
        border: 2px solid var(--gold) !important;
        box-shadow: 0 0 10px rgba(201, 162, 39, 0.4);
    }
    .click-assign-active .accordion-item {
        cursor: pointer;
    }
    .click-assign-active .accordion-item:hover {
        background: rgba(201, 162, 39, 0.15) !important;
    }
    .click-assign-hint {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--gold);
        color: #000;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: 600;
        z-index: 1050;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        display: none;
        animation: pulse-hint 1.5s infinite;
    }
    @keyframes pulse-hint {
        0%, 100% { transform: translateX(-50%) scale(1); }
        50% { transform: translateX(-50%) scale(1.05); }
    }
"""

# Insert CSS before the first closing </style>
style_end = content.find("</style>")
if style_end != -1:
    content = content[:style_end] + css_addition + "\n" + content[style_end:]
    print("CSS added")

# 2. Add auto-scroll JS and click-to-assign mode
js_addition = """
<script>
// ====== AUTO-SCROLL DURING DRAG ======
(function() {
    const SCROLL_SPEED = 8;
    const EDGE_SIZE = 60;
    let scrollInterval = null;

    function getScrollableParent(el) {
        while (el) {
            if (el.scrollHeight > el.clientHeight &&
                (getComputedStyle(el).overflowY === 'auto' || getComputedStyle(el).overflowY === 'scroll')) {
                return el;
            }
            el = el.parentElement;
        }
        return null;
    }

    // Auto-scroll the right panel when dragging near edges
    document.addEventListener('dragover', function(e) {
        // Find the right panel's scrollable area
        const rightPanel = document.querySelector('#typeTabsContent')?.closest('.card-body');
        if (!rightPanel) return;

        const rect = rightPanel.getBoundingClientRect();
        const y = e.clientY;

        if (scrollInterval) {
            clearInterval(scrollInterval);
            scrollInterval = null;
        }

        if (y > rect.top && y < rect.top + EDGE_SIZE && rightPanel.scrollTop > 0) {
            // Near top edge - scroll up
            scrollInterval = setInterval(() => {
                rightPanel.scrollTop -= SCROLL_SPEED;
            }, 16);
        } else if (y < rect.bottom && y > rect.bottom - EDGE_SIZE &&
                   rightPanel.scrollTop < rightPanel.scrollHeight - rightPanel.clientHeight) {
            // Near bottom edge - scroll down
            scrollInterval = setInterval(() => {
                rightPanel.scrollTop += SCROLL_SPEED;
            }, 16);
        }

        // Also auto-scroll the left panel
        const leftPanel = document.getElementById('practitionerListContainer');
        if (leftPanel) {
            const lRect = leftPanel.getBoundingClientRect();
            if (y > lRect.top && y < lRect.top + EDGE_SIZE && leftPanel.scrollTop > 0) {
                leftPanel.scrollTop -= SCROLL_SPEED;
            } else if (y < lRect.bottom && y > lRect.bottom - EDGE_SIZE) {
                leftPanel.scrollTop += SCROLL_SPEED;
            }
        }
    });

    document.addEventListener('dragend', function() {
        if (scrollInterval) {
            clearInterval(scrollInterval);
            scrollInterval = null;
        }
    });

    document.addEventListener('drop', function() {
        if (scrollInterval) {
            clearInterval(scrollInterval);
            scrollInterval = null;
        }
    });
})();

// ====== CLICK-TO-ASSIGN MODE ======
// Alternative to drag & drop: click practitioner, then click category
(function() {
    let selectedRegistrationId = null;
    let selectedElement = null;

    // Create hint banner
    const hint = document.createElement('div');
    hint.className = 'click-assign-hint';
    hint.innerHTML = '<i class="fas fa-hand-pointer me-2"></i>Cliquez sur une catégorie pour affecter';
    document.body.appendChild(hint);

    // Click on practitioner to select
    document.addEventListener('click', function(e) {
        const item = e.target.closest('.practitioner-drag-item');
        if (!item) return;

        // If already selected, deselect
        if (item.classList.contains('selected-for-assign')) {
            item.classList.remove('selected-for-assign');
            selectedRegistrationId = null;
            selectedElement = null;
            hint.style.display = 'none';
            document.getElementById('dragDropInterface')?.classList.remove('click-assign-active');
            return;
        }

        // Deselect previous
        document.querySelectorAll('.practitioner-drag-item.selected-for-assign').forEach(
            el => el.classList.remove('selected-for-assign')
        );

        // Select this one
        item.classList.add('selected-for-assign');
        selectedRegistrationId = item.dataset.registrationId;
        selectedElement = item;
        hint.style.display = 'block';
        hint.querySelector('i').nextSibling.textContent = ' ' + item.querySelector('.practitioner-name').textContent + ' → Cliquez sur une catégorie';
        document.getElementById('dragDropInterface')?.classList.add('click-assign-active');
    });

    // Click on accordion header to assign
    document.addEventListener('click', function(e) {
        if (!selectedRegistrationId) return;

        const accordionItem = e.target.closest('.accordion-item.category-accordion-item');
        if (!accordionItem) return;

        // Don't interfere if clicking the remove button
        if (e.target.closest('.btn-remove-from-category')) return;

        const categoryId = accordionItem.dataset.categoryId;
        const categoryName = accordionItem.dataset.categoryName;
        const dropZone = accordionItem.querySelector('.category-drop-zone');
        const practitionerName = selectedElement ? selectedElement.querySelector('.practitioner-name').textContent : '';

        if (categoryId && typeof assignToCategory === 'function') {
            assignToCategory(selectedRegistrationId, categoryId, practitionerName, categoryName, dropZone);

            // Keep selected for multi-assign (user can assign same practitioner to multiple categories)
            // Flash feedback
            accordionItem.style.transition = 'background 0.3s';
            accordionItem.style.background = 'rgba(40, 167, 69, 0.3)';
            setTimeout(() => { accordionItem.style.background = ''; }, 800);
        }
    });

    // Escape to cancel selection
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && selectedRegistrationId) {
            document.querySelectorAll('.practitioner-drag-item.selected-for-assign').forEach(
                el => el.classList.remove('selected-for-assign')
            );
            selectedRegistrationId = null;
            selectedElement = null;
            hint.style.display = 'none';
            document.getElementById('dragDropInterface')?.classList.remove('click-assign-active');
        }
    });
})();
</script>
"""

# Insert JS before the last </body> or last {% endblock %}
last_endblock = content.rfind("{% endblock %}")
if last_endblock != -1:
    content = content[:last_endblock] + js_addition + "\n" + content[last_endblock:]
    print("JS added")

with open(filepath, "w") as f:
    f.write(content)

print("DONE - Auto-scroll + click-to-assign deployed")
