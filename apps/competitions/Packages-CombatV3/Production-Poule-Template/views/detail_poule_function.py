# Fonction detail_poule améliorée pour le template professionnel
# À intégrer dans apps/competitions/views/combat.py

@login_required
def detail_poule(request, poule_id):
    """
    Affiche les détails d'une poule, y compris les équipes/participants et les combats.
    Version améliorée avec calcul des statistiques côté serveur.
    """
    poule = get_object_or_404(Poule, id=poule_id)
    combats = Combat.objects.filter(poule=poule).order_by('date_planifiee')
    
    # Calculer les statistiques
    total_combats = combats.count()
    combats_termines = combats.filter(status='termine').count()
    combats_en_cours = combats.filter(status='en_cours').count()
    combats_planifies = combats.filter(status='planifie').count()
    
    return render(request, 'competitions/combat/detail_poule.html', {
        'poule': poule,
        'combats': combats,
        'equipes': poule.equipes.all(),
        'pratiquants': poule.pratiquants.all(),
        'total_combats': total_combats,
        'combats_termines': combats_termines,
        'combats_en_cours': combats_en_cours,
        'combats_planifies': combats_planifies,
    })
