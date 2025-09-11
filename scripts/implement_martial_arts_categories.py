#!/usr/bin/env python3
"""
Script pour implémenter la structure complète des catégories d'arts martiaux
basée sur le fichier martial_arts_shop_categories.md
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from shop.models.category import Category
from competitions.models import Discipline

def create_martial_arts_categories():
    """
    Crée la structure complète des catégories d'équipement d'arts martiaux
    selon le fichier de spécification.
    """
    print("🥋 Implémentation des catégories MartialComp selon le fichier de spécification...")
    print("=" * 80)
    
    # Structure complète des catégories selon le fichier MD
    categories_structure = [
        # 1. TENUES & KIMONOS
        {
            'name': 'Tenues & Kimonos',
            'description': 'Tenues traditionnelles et modernes pour tous les arts martiaux',
            'order': 1,
            'children': [
                {
                    'name': 'Kimonos Karaté',
                    'description': 'Kimonos spécialisés pour la pratique du karaté',
                    'disciplines': ['Karaté'],
                    'products': [
                        'Kimono débutant (coton léger)',
                        'Kimono compétition (coton lourd 12-16oz)',
                        'Kimono kata (coupe spéciale, tissu premium)',
                        'Kimono club (personnalisable, logo)'
                    ]
                },
                {
                    'name': 'Judogi',
                    'description': 'Tenues officielles pour la pratique du judo',
                    'disciplines': ['Judo'],
                    'products': [
                        'Judogi débutant (coton simple)',
                        'Judogi compétition IJF (homologué)',
                        'Judogi entraînement (renforcé)'
                    ]
                },
                {
                    'name': 'Dobok Taekwondo',
                    'description': 'Tenues traditionnelles de taekwondo',
                    'disciplines': ['Taekwondo'],
                    'products': [
                        'Dobok traditionnel (col en V)',
                        'Dobok WTF (compétition)',
                        'Dobok ITF (style traditionnel)'
                    ]
                },
                {
                    'name': 'Tenues Arts Martiaux Mixtes',
                    'description': 'Équipements pour MMA et grappling',
                    'disciplines': ['MMA', 'Jiu-Jitsu Brésilien'],
                    'products': [
                        'Kimono JJB (grappling)',
                        'Rashguard manches longues/courtes',
                        'Shorts MMA/grappling'
                    ]
                },
                {
                    'name': 'Tenues Qwan Ki Do',
                    'description': 'Tenues traditionnelles complètes Qwan Ki Do',
                    'disciplines': ['Qwan Ki Do'],
                    'products': [
                        'Tenue traditionnelle complète',
                        'Pantalon noir réglementaire',
                        'Veste boutonnée traditionnelle'
                    ]
                },
                {
                    'name': 'Tenues Arts Chinois',
                    'description': 'Tenues pour Kung Fu, Tai Chi et Wushu',
                    'disciplines': ['Kung Fu', 'Tai Chi', 'Wushu'],
                    'products': [
                        'Tenue traditionnelle soie/coton',
                        'Tenue Tai Chi',
                        'Tenue Wushu compétition'
                    ]
                },
                {
                    'name': 'Tenues Aikido',
                    'description': 'Keikogi et hakama pour Aikido',
                    'disciplines': ['Aikido'],
                    'products': [
                        'Keikogi (veste + pantalon)',
                        'Hakama (jupe-pantalon traditionnelle)'
                    ]
                }
            ]
        },
        
        # 2. GRADES & CEINTURES
        {
            'name': 'Grades & Ceintures',
            'description': 'Ceintures et accessoires de graduation pour toutes les disciplines',
            'order': 2,
            'children': [
                {
                    'name': 'Ceintures Karaté',
                    'description': 'Système de grades karaté complet',
                    'disciplines': ['Karaté'],
                    'products': [
                        'Ceintures Kyu (couleurs)',
                        'Ceintures Dan (noires)',
                        'Broderie personnalisée'
                    ]
                },
                {
                    'name': 'Ceintures Judo',
                    'description': 'Ceintures homologuées IJF',
                    'disciplines': ['Judo'],
                    'products': [
                        'Système couleur international',
                        'Ceintures homologuées IJF',
                        'Ceintures maître (rouge/blanc, rouge)'
                    ]
                },
                {
                    'name': 'Ceintures Taekwondo',
                    'description': 'Systèmes WTF/WT et ITF',
                    'disciplines': ['Taekwondo'],
                    'products': [
                        'Système WTF/WT',
                        'Système ITF',
                        'Ceintures spéciales (Poom, Dan)'
                    ]
                },
                {
                    'name': 'Autres Systèmes de Grades',
                    'description': 'Grades pour autres disciplines',
                    'disciplines': ['Qwan Ki Do', 'Aikido', 'Jiu-Jitsu Brésilien'],
                    'products': [
                        'Qwan Ki Do (caps colorés + dangs)',
                        'Aikido (kyu + dan + hakama)',
                        'JJB (système brésilien)'
                    ]
                },
                {
                    'name': 'Accessoires Grades',
                    'description': 'Accessoires pour la gestion des grades',
                    'products': [
                        'Barrettes de grade',
                        'Galons de grade',
                        'Certificats de passage de grade',
                        'Livrets de grade personnalisés'
                    ]
                }
            ]
        },
        
        # 3. PROTECTIONS & SÉCURITÉ
        {
            'name': 'Protections & Sécurité',
            'description': 'Équipements de protection pour un entraînement sécurisé',
            'order': 3,
            'children': [
                {
                    'name': 'Protections Tête',
                    'description': 'Casques et protections pour la tête',
                    'products': [
                        'Casques karaté (rouge/bleu)',
                        'Casques taekwondo WTF/ITF',
                        'Protège-dents (simple, double, sur-mesure)',
                        'Protections faciales (escrime, kendo)'
                    ]
                },
                {
                    'name': 'Protections Corps',
                    'description': 'Plastrons et protections corporelles',
                    'products': [
                        'Plastrons karaté/taekwondo',
                        'Protège-poitrine féminin',
                        'Coquilles (homme/femme/enfant)',
                        'Protège-avant-bras'
                    ]
                },
                {
                    'name': 'Protections Membres',
                    'description': 'Gants et protections pour jambes/pieds',
                    'products': [
                        'Gants karaté (mitaines, kumite)',
                        'Gants boxe/kickboxing',
                        'Protège-tibias (karaté, muay thai)',
                        'Protège-pieds (karaté, taekwondo)',
                        'Chevillières, genouillères'
                    ]
                },
                {
                    'name': 'Matériel de Sécurité',
                    'description': 'Équipements de premiers secours',
                    'products': [
                        'Trousses de premiers secours',
                        'Packs de glace instantanée',
                        'Bandes de strapping',
                        'Désinfectants'
                    ]
                }
            ]
        },
        
        # 4. MATÉRIEL D'ENTRAÎNEMENT
        {
            'name': 'Matériel d\'Entraînement',
            'description': 'Équipements pour l\'entraînement et le perfectionnement technique',
            'order': 4,
            'children': [
                {
                    'name': 'Sacs & Makiwara',
                    'description': 'Sacs de frappe et makiwara traditionnels',
                    'products': [
                        'Sacs lourds (30-80kg)',
                        'Sacs de vitesse',
                        'Sacs de sol (grappling)',
                        'Supports et chaînes',
                        'Makiwara traditionnel',
                        'Pattes d\'ours',
                        'Paos (thaï pads)',
                        'Boucliers de frappe'
                    ]
                },
                {
                    'name': 'Armes Traditionnelles',
                    'description': 'Armes d\'entraînement pour arts martiaux',
                    'disciplines': ['Aikido', 'Karaté', 'Kobudo'],
                    'products': [
                        'Boken (sabre bois)',
                        'Jo (bâton court)',
                        'Bo (bâton long)',
                        'Nunchaku (mousse, bois, métal)',
                        'Sai, tonfa, kama'
                    ]
                },
                {
                    'name': 'Matériel Souplesse',
                    'description': 'Équipements pour améliorer la flexibilité',
                    'products': [
                        'Barres de stretching',
                        'Sangles d\'étirement',
                        'Tapis de sol épais',
                        'Blocs de yoga'
                    ]
                },
                {
                    'name': 'Matériel Pédagogique',
                    'description': 'Supports d\'apprentissage et formation',
                    'products': [
                        'Planches anatomiques',
                        'Schémas techniques plastifiés',
                        'Vidéos pédagogiques',
                        'Livres techniques par discipline'
                    ]
                }
            ]
        },
        
        # 5. ÉQUIPEMENT DOJO/CLUB
        {
            'name': 'Équipement Dojo/Club',
            'description': 'Installations et équipements pour dojos et clubs',
            'order': 5,
            'children': [
                {
                    'name': 'Tatamis & Sols',
                    'description': 'Revêtements de sol pour arts martiaux',
                    'products': [
                        'Tatamis puzzle (20mm, 30mm, 40mm)',
                        'Tatamis pliables',
                        'Tatamis de compétition homologués',
                        'Bordures et angles',
                        'Tapis de lutte',
                        'Aires de combat officielles',
                        'Revêtements anti-dérapants'
                    ]
                },
                {
                    'name': 'Mobilier Dojo',
                    'description': 'Mobilier pour équiper les dojos',
                    'products': [
                        'Gradins télescopiques',
                        'Chaises arbitres',
                        'Tables de marque',
                        'Tableaux d\'affichage'
                    ]
                },
                {
                    'name': 'Sonorisation',
                    'description': 'Équipements audio et chronométrage',
                    'products': [
                        'Chronomètres électroniques',
                        'Gongs et clochettes',
                        'Micros sans fil',
                        'Systèmes de sonorisation'
                    ]
                },
                {
                    'name': 'Matériel Arbitrage',
                    'description': 'Équipements pour l\'arbitrage et compétitions',
                    'products': [
                        'Drapeaux arbitres (rouge/blanc)',
                        'Cartons d\'avertissement',
                        'Chronomètres officiels',
                        'Carnets de notation'
                    ]
                },
                {
                    'name': 'Organisation Événements',
                    'description': 'Matériel pour organiser compétitions et stages',
                    'products': [
                        'Panneaux signalétiques',
                        'Barrières de délimitation',
                        'Banderoles personnalisées',
                        'Badges et lanyards'
                    ]
                }
            ]
        },
        
        # 6. LIVRES & MÉDIAS
        {
            'name': 'Livres & Médias',
            'description': 'Documentation technique et pédagogique',
            'order': 6,
            'children': [
                {
                    'name': 'Manuels Techniques',
                    'description': 'Livres techniques par discipline',
                    'products': [
                        'Karaté : katas, bunkai, histoire',
                        'Judo : techniques, randori, kata',
                        'Taekwondo : poomsae, techniques',
                        'Arts chinois : formes, philosophie'
                    ]
                },
                {
                    'name': 'Médias Numériques',
                    'description': 'Supports numériques d\'apprentissage',
                    'products': [
                        'DVD/Blu-ray techniques',
                        'Formations en ligne',
                        'Applications mobiles',
                        'Codes d\'accès plateformes'
                    ]
                },
                {
                    'name': 'Histoire & Philosophie',
                    'description': 'Culture et philosophie des arts martiaux',
                    'products': [
                        'Biographies de maîtres',
                        'Histoire des arts martiaux',
                        'Philosophie orientale',
                        'Méditation et spiritualité'
                    ]
                }
            ]
        },
        
        # 7. TROPHÉES & RÉCOMPENSES
        {
            'name': 'Trophées & Récompenses',
            'description': 'Récompenses pour compétitions et passages de grades',
            'order': 7,
            'children': [
                {
                    'name': 'Trophées & Coupes',
                    'description': 'Trophées pour compétitions',
                    'products': [
                        'Arts martiaux génériques',
                        'Spécifiques par discipline',
                        'Personnalisables (gravure)',
                        'Différentes tailles/budgets'
                    ]
                },
                {
                    'name': 'Médailles & Diplômes',
                    'description': 'Médailles et certificats de récompense',
                    'products': [
                        'Médailles compétition (or, argent, bronze)',
                        'Médailles participation',
                        'Diplômes et certificats',
                        'Pins et badges de club'
                    ]
                },
                {
                    'name': 'Coupes & Challenges',
                    'description': 'Coupes spéciales et challenges',
                    'products': [
                        'Coupes individuelles',
                        'Coupes par équipes',
                        'Challenges perpétuels',
                        'Plaques commémoratives'
                    ]
                }
            ]
        },
        
        # 8. ACCESSOIRES & LIFESTYLE
        {
            'name': 'Accessoires & Lifestyle',
            'description': 'Accessoires et produits lifestyle arts martiaux',
            'order': 8,
            'children': [
                {
                    'name': 'Bagagerie',
                    'description': 'Sacs et housses de transport',
                    'products': [
                        'Sacs karaté traditionnels',
                        'Sacs à dos martial arts',
                        'Housses pour armes',
                        'Valises de compétition'
                    ]
                },
                {
                    'name': 'Textile Casual',
                    'description': 'Vêtements décontractés arts martiaux',
                    'products': [
                        'T-shirts clubs/disciplines',
                        'Sweats à capuche',
                        'Casquettes et bonnets',
                        'Polo clubs personnalisés'
                    ]
                },
                {
                    'name': 'Bien-être',
                    'description': 'Produits de bien-être pour sportifs',
                    'products': [
                        'Huiles de massage',
                        'Baumes chauffants',
                        'Compléments alimentaires',
                        'Matériel de récupération'
                    ]
                }
            ]
        },
        
        # 9. SANTÉ & RÉCUPÉRATION
        {
            'name': 'Santé & Récupération',
            'description': 'Produits pour la santé et récupération des sportifs',
            'order': 9,
            'children': [
                {
                    'name': 'Soins & Traitements',
                    'description': 'Produits de soin pour sportifs',
                    'products': [
                        'Pommades anti-inflammatoires',
                        'Patchs chauffants/rafraîchissants',
                        'Bandes élastiques',
                        'Matériel kinésithérapie'
                    ]
                },
                {
                    'name': 'Nutrition Sportive',
                    'description': 'Compléments nutritionnels',
                    'products': [
                        'Protéines en poudre',
                        'Boissons énergétiques',
                        'Barres nutritionnelles',
                        'Compléments récupération'
                    ]
                }
            ]
        },
        
        # 10. PERSONNALISATION & SERVICES
        {
            'name': 'Personnalisation & Services',
            'description': 'Services de personnalisation et commandes spéciales',
            'order': 10,
            'children': [
                {
                    'name': 'Broderie & Marquage',
                    'description': 'Services de personnalisation textile',
                    'products': [
                        'Broderie noms/logos sur kimonos',
                        'Impression textile',
                        'Gravure trophées',
                        'Patches et écussons'
                    ]
                },
                {
                    'name': 'Services Club',
                    'description': 'Services dédiés aux clubs et fédérations',
                    'products': [
                        'Commandes groupées clubs',
                        'Devis personnalisés',
                        'Livraison sur site',
                        'Formation utilisation matériel'
                    ]
                }
            ]
        }
    ]
    
    created_count = 0
    
    try:
        with transaction.atomic():
            print("📋 Création des catégories principales et sous-catégories...")
            
            for category_data in categories_structure:
                # Créer la catégorie principale
                main_category, created = Category.objects.get_or_create(
                    name=category_data['name'],
                    defaults={
                        'description': category_data['description'],
                        'is_active': True,
                        'order': category_data.get('order', 0)
                    }
                )
                
                if created:
                    created_count += 1
                    print(f"✅ Catégorie principale créée: {main_category.name}")
                else:
                    print(f"ℹ️  Catégorie principale existe: {main_category.name}")
                
                # Créer les sous-catégories
                for i, child_data in enumerate(category_data.get('children', [])):
                    child_category, created = Category.objects.get_or_create(
                        name=child_data['name'],
                        parent=main_category,
                        defaults={
                            'description': child_data['description'],
                            'is_active': True,
                            'order': i
                        }
                    )
                    
                    if created:
                        created_count += 1
                        print(f"  ✅ Sous-catégorie créée: {child_category.name}")
                        
                        # Associer aux disciplines si spécifiées
                        if 'disciplines' in child_data:
                            try:
                                disciplines = Discipline.objects.filter(
                                    name__in=child_data['disciplines']
                                )
                                if disciplines.exists():
                                    child_category.disciplines.set(disciplines)
                                    print(f"    🔗 Associée aux disciplines: {', '.join([d.name for d in disciplines])}")
                            except Exception as e:
                                print(f"    ⚠️  Erreur association disciplines: {e}")
                    else:
                        print(f"  ℹ️  Sous-catégorie existe: {child_category.name}")
            
            print(f"\n🎉 Terminé ! {created_count} nouvelles catégories créées.")
            print(f"📊 Total catégories: {Category.objects.count()}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        raise

def show_category_tree():
    """
    Affiche l'arbre des catégories créées.
    """
    print("\n" + "=" * 80)
    print("📋 STRUCTURE DES CATÉGORIES CRÉÉES")
    print("=" * 80)
    
    try:
        main_categories = Category.objects.filter(parent=None).order_by('order', 'name')
        
        for main_cat in main_categories:
            print(f"\n🔸 {main_cat.name}")
            print(f"   {main_cat.description}")
            
            sub_categories = main_cat.children.all().order_by('order', 'name')
            for sub_cat in sub_categories:
                disciplines_list = ", ".join([d.name for d in sub_cat.disciplines.all()])
                disciplines_info = f" [{disciplines_list}]" if disciplines_list else ""
                print(f"   → {sub_cat.name}{disciplines_info}")
                
        print(f"\n📊 Résumé:")
        print(f"   • Catégories principales: {main_categories.count()}")
        print(f"   • Sous-catégories: {Category.objects.filter(parent__isnull=False).count()}")
        print(f"   • Total: {Category.objects.count()}")
                
    except Exception as e:
        print(f"❌ Erreur lors de l'affichage: {e}")

def verify_implementation():
    """
    Vérifie que l'implémentation est correcte.
    """
    print("\n" + "=" * 80)
    print("✅ VÉRIFICATION DE L'IMPLÉMENTATION")
    print("=" * 80)
    
    checks = [
        ("Catégories principales", lambda: Category.objects.filter(parent=None).count() >= 10),
        ("Sous-catégories", lambda: Category.objects.filter(parent__isnull=False).count() >= 30),
        ("Catégories actives", lambda: Category.objects.filter(is_active=True).count() >= 40),
        ("Associations disciplines", lambda: any(cat.disciplines.exists() for cat in Category.objects.all())),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{check_name}: {status}")
            if not result:
                all_passed = False
        except Exception as e:
            print(f"{check_name}: ❌ ERREUR - {e}")
            all_passed = False
    
    print(f"\n{'🎉 IMPLÉMENTATION RÉUSSIE' if all_passed else '⚠️  PROBLÈMES DÉTECTÉS'}")
    return all_passed

if __name__ == '__main__':
    try:
        print("🚀 Démarrage de l'implémentation des catégories MartialComp...")
        
        create_martial_arts_categories()
        show_category_tree()
        success = verify_implementation()
        
        if success:
            print(f"\n{'=' * 80}")
            print("🎯 IMPLÉMENTATION TERMINÉE AVEC SUCCÈS !")
            print("=" * 80)
            print("\n🌐 Testez maintenant:")
            print("   • Formulaire de création: http://127.0.0.1:8000/shop/dashboard/club/product/create/")
            print("   • Administration: http://127.0.0.1:8000/admin/shop/category/")
            print("\n📝 Plus de 40 catégories spécialisées sont maintenant disponibles !")
        else:
            print("\n⚠️  L'implémentation s'est terminée avec des avertissements.")
            
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)