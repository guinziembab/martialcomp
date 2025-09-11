from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from apps.finances.models.pricing import PricingRegion, VolumeDiscount
from decimal import Decimal
import json
from datetime import date, timedelta
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@csrf_exempt
@require_http_methods(["POST"])
def calculate_pricing(request):
    """API pour calculer la tarification selon région et nombre de membres"""
    try:
        data = json.loads(request.body)
        region_code = data.get('region')
        member_count = int(data.get('member_count', 1))
        
        # Validation
        if member_count < 1:
            return JsonResponse({'error': 'Nombre de membres invalide'}, status=400)
        
        # Récupérer la région
        try:
            region = PricingRegion.objects.get(name=region_code, is_active=True)
        except PricingRegion.DoesNotExist:
            return JsonResponse({'error': 'Région non trouvée'}, status=404)
        
        # Calculer la tarification
        base_price = region.base_price_per_member
        volume_discount = VolumeDiscount.get_discount_for_members(member_count)
        discount_amount = base_price * (volume_discount / 100)
        final_price_per_member = base_price - discount_amount
        total_amount = final_price_per_member * member_count
        
        # Informations sur la réduction
        discount_info = None
        if volume_discount > 0:
            discount_range = VolumeDiscount.objects.filter(
                member_range_start__lte=member_count,
                member_range_end__gte=member_count
            ).first()
            
            if not discount_range:
                discount_range = VolumeDiscount.objects.filter(
                    member_range_start__lte=member_count,
                    member_range_end=0
                ).first()
            
            if discount_range:
                discount_info = {
                    'range': f"{discount_range.member_range_start}-{discount_range.member_range_end if discount_range.member_range_end > 0 else '+'} membres",
                    'description': discount_range.description
                }
        
        return JsonResponse({
            'region': {
                'name': region.get_name_display(),
                'code': region.name,
                'currency': region.currency
            },
            'member_count': member_count,
            'pricing': {
                'base_price_per_member': float(base_price),
                'volume_discount_percentage': float(volume_discount),
                'final_price_per_member': float(final_price_per_member),
                'total_amount': float(total_amount),
                'savings': float(base_price * member_count - total_amount)
            },
            'discount_info': discount_info,
            'installment_options': [
                {'count': 1, 'amount': float(total_amount)},
                {'count': 3, 'amount': float(total_amount / 3)},
                {'count': 4, 'amount': float(total_amount / 4)}
            ]
        })
        
    except (ValueError, KeyError) as e:
        return JsonResponse({'error': f'Données invalides: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)

@require_http_methods(["GET"])
def get_regions(request):
    """API pour récupérer la liste des régions disponibles"""
    regions = PricingRegion.objects.filter(is_active=True).values('name', 'base_price_per_member', 'currency')
    
    regions_data = []
    for region in regions:
        regions_data.append({
            'code': region['name'],
            'name': dict(PricingRegion.REGION_CHOICES)[region['name']],
            'base_price': float(region['base_price_per_member']),
            'currency': region['currency']
        })
    
    return JsonResponse({'regions': regions_data})

@require_http_methods(["GET"])
def get_volume_discounts(request):
    """API pour récupérer les réductions volume"""
    discounts = get_organization_queryset(VolumeDiscount, self.request.user).order_by('member_range_start')
    
    discounts_data = []
    for discount in discounts:
        end_range = discount.member_range_end if discount.member_range_end > 0 else '+'
        discounts_data.append({
            'range': f"{discount.member_range_start}-{end_range}",
            'percentage': float(discount.discount_percentage),
            'description': discount.description
        })
    
    return JsonResponse({'discounts': discounts_data})

@csrf_exempt
@require_http_methods(["POST"])
def create_subscription_quote(request):
    """Crée un devis de souscription"""
    try:
        data = json.loads(request.body)
        organization_id = data.get('organization_id')
        region_code = data.get('region')
        member_count = int(data.get('member_count', 1))
        installment_count = int(data.get('installment_count', 1))
        
        # Validation
        if installment_count not in [1, 3, 4]:
            return JsonResponse({'error': 'Nombre de versements invalide'}, status=400)
        
        # Calculer la tarification
        pricing_response = calculate_pricing(request)
        if pricing_response.status_code != 200:
            return pricing_response
        
        pricing_data = json.loads(pricing_response.content)
        
        # Créer le devis
        from apps.finances.models.subscription import Subscription
        
        quote = {
            'organization_id': organization_id,
            'region': pricing_data['region'],
            'member_count': member_count,
            'pricing': pricing_data['pricing'],
            'installment_count': installment_count,
            'installment_amount': pricing_data['pricing']['total_amount'] / installment_count,
            'valid_until': (date.today() + timedelta(days=30)).isoformat()
        }
        
        return JsonResponse({'quote': quote})
        
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors de la création du devis: {str(e)}'}, status=500) 

