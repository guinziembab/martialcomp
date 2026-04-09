// Script de test pour vérifier les boutons du dashboard
// À exécuter dans la console du navigateur

console.log("=== TEST DES BOUTONS DU DASHBOARD ===");

// 1. Vérifier que getCookie existe
console.log("1. Test getCookie:");
if (typeof getCookie === 'function') {
    console.log("✅ getCookie est définie");
    console.log("   CSRF Token:", getCookie('csrftoken'));
} else {
    console.error("❌ getCookie n'est pas définie");
}

// 2. Vérifier les URLs Django
console.log("\n2. Test des URLs Django:");
if (typeof DJANGO_URLS !== 'undefined') {
    console.log("✅ DJANGO_URLS est définie");
    console.log("   - practitioner_delete:", DJANGO_URLS.practitioner_delete);
    console.log("   - practitioner_toggle_status:", DJANGO_URLS.practitioner_toggle_status);
    console.log("   - import_export:", DJANGO_URLS.import_export);
} else {
    console.error("❌ DJANGO_URLS n'est pas définie");
}

// 3. Vérifier les traductions
console.log("\n3. Test des traductions Django:");
if (typeof DJANGO_TRANS !== 'undefined') {
    console.log("✅ DJANGO_TRANS est définie");
    console.log("   Nombre de traductions:", Object.keys(DJANGO_TRANS).length);
} else {
    console.error("❌ DJANGO_TRANS n'est pas définie");
}

// 4. Compter les boutons
console.log("\n4. Comptage des boutons:");
const deleteButtons = document.querySelectorAll('.delete-practitioner-btn');
const toggleButtons = document.querySelectorAll('.toggle-status-btn');
const importBtn = document.getElementById('importCsvBtn');
const bulkBtn = document.getElementById('bulkRegistrationBtn');

console.log(`   - Boutons suppression: ${deleteButtons.length}`);
console.log(`   - Boutons toggle status: ${toggleButtons.length}`);
console.log(`   - Bouton Import CSV: ${importBtn ? '✅ Trouvé' : '❌ Non trouvé'}`);
console.log(`   - Bouton Inscription masse: ${bulkBtn ? '✅ Trouvé' : '❌ Non trouvé'}`);

// 5. Vérifier les attributs d'un bouton de suppression
console.log("\n5. Test d'un bouton de suppression:");
if (deleteButtons.length > 0) {
    const firstDeleteBtn = deleteButtons[0];
    console.log("   - practitioner-id:", firstDeleteBtn.getAttribute('data-practitioner-id'));
    console.log("   - practitioner-name:", firstDeleteBtn.getAttribute('data-practitioner-name'));
    console.log("   - Classes CSS:", firstDeleteBtn.className);
} else {
    console.log("   ⚠️ Aucun bouton de suppression trouvé");
}

// 6. Vérifier les attributs d'un bouton toggle
console.log("\n6. Test d'un bouton toggle status:");
if (toggleButtons.length > 0) {
    const firstToggleBtn = toggleButtons[0];
    console.log("   - practitioner-id:", firstToggleBtn.getAttribute('data-practitioner-id'));
    console.log("   - current-status:", firstToggleBtn.getAttribute('data-current-status'));
    console.log("   - Classes CSS:", firstToggleBtn.className);
} else {
    console.log("   ⚠️ Aucun bouton toggle trouvé");
}

// 7. Simuler un clic sur un bouton (sans vraiment supprimer)
console.log("\n7. Test de simulation de clic:");
console.log("   Pour tester un bouton de suppression, exécutez:");
console.log("   document.querySelector('.delete-practitioner-btn').click()");
console.log("   ");
console.log("   Pour tester un bouton toggle, exécutez:");
console.log("   document.querySelector('.toggle-status-btn').click()");

console.log("\n=== FIN DES TESTS ===");
console.log("Si tous les tests sont ✅, les boutons devraient fonctionner.");
console.log("Sinon, vérifiez les erreurs ❌ ci-dessus.");