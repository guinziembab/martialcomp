# apps/competitions/views/demo_numpad.py
"""
PROMPT 9 - Vue de démonstration pour le pavé numérique de notation.
Permet de tester l'interface sans données réelles.
À utiliser uniquement en environnement de développement.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import random


# Données de démonstration simulées
# IMPORTANT: Pour la neutralité des juges, on n'affiche PAS le club ni le pays
# Seulement: Nom, Prénom, Grade, Âge + Photo
DEMO_PRACTITIONERS = [
    {"id": 1, "name": "Marie Dubois", "grade": "1er Dan", "age": 24,
     "license": "2024-001", "photo": None},
    {"id": 2, "name": "Pierre Martin", "grade": "2ème Dan", "age": 28,
     "license": "2024-015", "photo": None},
    {"id": 3, "name": "Sophie Bernard", "grade": "1er Dan", "age": 22,
     "license": "2024-042", "photo": None},
    {"id": 4, "name": "Lucas Petit", "grade": "3ème Dan", "age": 31,
     "license": "2024-007", "photo": None},
    {"id": 5, "name": "Emma Leroy", "grade": "1er Dan", "age": 19,
     "license": "2024-023", "photo": None},
    {"id": 6, "name": "Hugo Moreau", "grade": "2ème Dan", "age": 26,
     "license": "2024-089", "photo": None},
    {"id": 7, "name": "Chloé Garcia", "grade": "1er Dan", "age": 21,
     "license": "2024-033", "photo": None},
    {"id": 8, "name": "Nathan Roux", "grade": "2ème Dan", "age": 25,
     "license": "2024-056", "photo": None},
]

DEMO_CRITERIA = [
    {
        "id": 1,
        "name": "Technique",
        "description": "Qualité d'exécution des mouvements techniques",
        "weight": 1.0,
        "min_score": 0,
        "max_score": 10,
        "step": 0.25
    },
    {
        "id": 2,
        "name": "Puissance",
        "description": "Force et impact des techniques",
        "weight": 0.8,
        "min_score": 0,
        "max_score": 10,
        "step": 0.25
    },
    {
        "id": 3,
        "name": "Présentation",
        "description": "Attitude, salut et comportement",
        "weight": 0.5,
        "min_score": 0,
        "max_score": 10,
        "step": 0.25
    },
]

# Stockage temporaire des scores de démo (en mémoire)
demo_scores = {}


def demo_numpad_view(request):
    """
    Vue de démonstration du pavé numérique.
    Affiche une feuille de notation avec des données simulées.
    """
    # Vérifier que nous sommes en mode DEBUG
    if not settings.DEBUG:
        from django.http import Http404
        raise Http404("Page de démonstration non disponible en production")

    # Générer des performances de démo
    # NEUTRALITÉ JUGE: Pas de club/pays, seulement Nom, Prénom, Grade, Âge
    performances = []
    for i, practitioner in enumerate(DEMO_PRACTITIONERS, 1):
        perf_id = practitioner["id"]

        # Vérifier si des scores existent déjà
        score = demo_scores.get(perf_id, {}).get("average")
        has_scored = score is not None

        # Créer l'objet pratiquant avec grade et âge (pas de club)
        pract_obj = type('obj', (object,), {
            "full_name": practitioner["name"],
            "license_number": practitioner["license"],
            "grade": practitioner["grade"],
            "age": practitioner["age"]
        })()

        performances.append({
            "performance": {"id": perf_id, "order": i},
            "practitioner": pract_obj,
            "has_scored": has_scored,
            "score": round(score, 2) if score else None,
            "display_status": "scored" if has_scored else "pending",
            "is_current": i == 3 and not has_scored,
        })

    # Statistiques
    scored_count = len([p for p in performances if p["has_scored"]])
    total_count = len(performances)
    scores_values = [p["score"] for p in performances if p["score"]]

    stats = {
        "scored_count": scored_count,
        "total_count": total_count,
        "progress_percent": round((scored_count / total_count * 100) if total_count > 0 else 0, 1),
        "average_score": round(sum(scores_values) / len(scores_values), 2) if scores_values else 0,
        "min_score": round(min(scores_values), 2) if scores_values else 0,
        "max_score": round(max(scores_values), 2) if scores_values else 0,
    }

    context = {
        "category": type('obj', (object,), {
            "id": 999,
            "name": "Kata Senior - Démonstration"
        })(),
        "competition": type('obj', (object,), {
            "name": "Championnat de Démonstration 2024",
            "title": "Championnat de Démonstration 2024"
        })(),
        "judge": type('obj', (object,), {
            "practitioner": type('obj', (object,), {"full_name": "Jean Dupont (Juge Demo)"})(),
            "get_qualification_level_display": lambda: "National"
        })(),
        "performances": performances,
        "stats": stats,
        "current_round": 1,
        "total_rounds": 2,
        "scoring_config": None,
        "all_scored": scored_count == total_count and total_count > 0,
        "is_live": True,
        "current_performance": None,
        "is_demo": True,  # Flag pour identifier le mode démo
    }

    return render(request, "competitions/technical_scoring/demo_scoring_sheet.html", context)


def demo_get_criteria(request, performance_id):
    """
    API de démonstration pour récupérer les critères d'une performance.
    """
    if not settings.DEBUG:
        return JsonResponse({"status": "error", "message": "Non disponible en production"}, status=404)

    # Trouver le pratiquant
    practitioner = next((p for p in DEMO_PRACTITIONERS if p["id"] == performance_id), None)
    if not practitioner:
        return JsonResponse({"status": "error", "message": "Performance non trouvée"}, status=404)

    # Récupérer les scores existants
    existing_scores = demo_scores.get(performance_id, {}).get("criteria", {})

    criteria_data = []
    for criterion in DEMO_CRITERIA:
        criteria_data.append({
            **criterion,
            "current_value": existing_scores.get(criterion["id"])
        })

    # NEUTRALITÉ JUGE: Pas de club, seulement nom, grade, âge et photo
    return JsonResponse({
        "status": "success",
        "performance": {
            "id": performance_id,
            "practitioner": practitioner["name"],
            "grade": practitioner["grade"],
            "age": practitioner["age"],
            "photo_url": practitioner.get("photo"),
            "order": performance_id,
            "status": "ready"
        },
        "criteria": criteria_data,
        "config": {
            "min_score": 0,
            "max_score": 10,
            "score_step": 0.25
        },
        "has_scored": len(existing_scores) > 0
    })


@csrf_exempt
def demo_save_score(request):
    """
    API de démonstration pour sauvegarder un score.
    Stocke les scores en mémoire (perdu au redémarrage).
    """
    if not settings.DEBUG:
        return JsonResponse({"success": False, "message": "Non disponible en production"}, status=404)

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée"}, status=405)

    try:
        data = json.loads(request.body)
        performance_id = data.get("performance_id")
        criterion_id = data.get("criterion_id")
        score_value = float(data.get("score", 0))
        comment = data.get("comment", "")

        # Valider
        if score_value < 0 or score_value > 10:
            return JsonResponse({"success": False, "message": "Score invalide"}, status=400)

        # Stocker le score
        if performance_id not in demo_scores:
            demo_scores[performance_id] = {"criteria": {}}

        demo_scores[performance_id]["criteria"][criterion_id] = score_value

        # Calculer la moyenne
        criteria_scores = demo_scores[performance_id]["criteria"]
        if criteria_scores:
            weighted_sum = 0
            total_weight = 0
            for crit in DEMO_CRITERIA:
                if crit["id"] in criteria_scores:
                    weighted_sum += criteria_scores[crit["id"]] * crit["weight"]
                    total_weight += crit["weight"]
            if total_weight > 0:
                demo_scores[performance_id]["average"] = weighted_sum / total_weight

        # Trouver le nom du critère
        criterion = next((c for c in DEMO_CRITERIA if c["id"] == criterion_id), {"name": "Inconnu"})
        practitioner = next((p for p in DEMO_PRACTITIONERS if p["id"] == performance_id), {"name": "Inconnu"})

        return JsonResponse({
            "success": True,
            "message": f"Score enregistré avec succès (Démo)",
            "data": {
                "score_id": random.randint(1000, 9999),
                "performance_id": performance_id,
                "criterion_id": criterion_id,
                "criterion_name": criterion["name"],
                "score": score_value,
                "comment": comment,
                "created": True,
                "practitioner": practitioner["name"],
                "total_score": demo_scores[performance_id].get("average")
            }
        })

    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


def demo_get_ranking(request, category_id):
    """
    API de démonstration pour le classement provisoire.
    """
    if not settings.DEBUG:
        return JsonResponse({"status": "error", "message": "Non disponible en production"}, status=404)

    # NEUTRALITÉ JUGE: Pas de club dans le classement
    # Inclure photo, grade et age pour l'affichage
    ranking = []
    for practitioner in DEMO_PRACTITIONERS:
        perf_id = practitioner["id"]
        if perf_id in demo_scores and "average" in demo_scores[perf_id]:
            ranking.append({
                "practitioner_id": perf_id,
                "practitioner_name": practitioner["name"],
                "grade": practitioner["grade"],
                "age": practitioner["age"],
                "photo_url": practitioner.get("photo"),
                "score": demo_scores[perf_id]["average"],
                "judges_count": 1
            })

    # Trier par score décroissant
    ranking.sort(key=lambda x: x["score"], reverse=True)

    # Ajouter les rangs
    for i, item in enumerate(ranking, 1):
        item["rank"] = i

    return JsonResponse({
        "status": "success",
        "category": "Kata Senior - Démonstration",
        "ranking": ranking
    })


def demo_reset_scores(request):
    """
    Réinitialiser tous les scores de démonstration.
    """
    if not settings.DEBUG:
        return JsonResponse({"success": False, "message": "Non disponible en production"}, status=404)

    global demo_scores
    demo_scores = {}

    return JsonResponse({
        "success": True,
        "message": "Scores de démonstration réinitialisés"
    })
