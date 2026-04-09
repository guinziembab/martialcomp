"""
Stripe payment views for MartialComp.

Views:
  - create_checkout: POST - Creates Stripe Checkout Session + pending Transaction/PaymentAttempt
  - stripe_webhook: POST - @csrf_exempt - Verifies signature, routes to handlers
  - checkout_success: GET - Informational success page (real update is via webhook)
  - checkout_cancel: GET - Cancellation page
"""
import json
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import get_language
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..models.payments import PaymentMethod, PaymentAttempt
from ..models.transactions import Transaction
from ..services.stripe_service import StripeService, StripeServiceError
from ..services.stripe_webhook_handler import StripeWebhookHandler

logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str:
    """Extract real client IP, respecting Cloudflare/proxy headers."""
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@login_required
@require_POST
def create_checkout(request):
    """
    Create a Stripe Checkout Session and redirect the user to Stripe's hosted page.

    Expected POST body (JSON):
    {
        "line_items": [
            {
                "name": "Inscription Competition Judo",
                "description": "Categorie -66kg Senior",
                "amount_cents": 2500,
                "currency": "eur",
                "quantity": 1
            }
        ],
        "metadata": {
            "type": "competition_registration",
            "competition_id": "42"
        },
        "customer_email": "user@example.com"  // optional
    }

    Creates Transaction (pending) + PaymentAttempt (initiated), then redirects to Stripe.
    """
    # Parse request body
    try:
        if request.content_type and 'application/json' in request.content_type:
            body = json.loads(request.body)
        else:
            body = request.POST.dict()
            if 'line_items' in body:
                body['line_items'] = json.loads(body['line_items'])
            if 'metadata' in body:
                body['metadata'] = json.loads(body['metadata'])
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("create_checkout: Invalid request body: %s", e)
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    line_items = body.get('line_items', [])
    metadata = body.get('metadata', {})
    customer_email = body.get('customer_email', '') or request.user.email

    if not line_items:
        return JsonResponse({'error': 'line_items is required'}, status=400)

    # Validate line_items
    for item in line_items:
        if not all(k in item for k in ('name', 'amount_cents', 'currency')):
            return JsonResponse(
                {'error': 'Each line_item needs: name, amount_cents, currency'},
                status=400,
            )
        if not isinstance(item['amount_cents'], int) or item['amount_cents'] <= 0:
            return JsonResponse(
                {'error': 'amount_cents must be a positive integer'},
                status=400,
            )

    # Build success/cancel URLs
    base_url = request.build_absolute_uri('/').rstrip('/')
    lang = get_language() or 'fr'

    success_url = (
        f"{base_url}/{lang}/finances/stripe/success/"
        f"?session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = f"{base_url}/{lang}/finances/stripe/cancel/"

    # Add user context to metadata
    metadata['user_id'] = str(request.user.id)

    # Create Stripe Checkout Session
    try:
        session = StripeService.create_checkout_session(
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={k: str(v) for k, v in metadata.items()},
            customer_email=customer_email,
            mode='payment',
        )
    except StripeServiceError as e:
        logger.error("create_checkout: StripeServiceError: %s", e)
        return JsonResponse({'error': str(e)}, status=502)

    # Get or create the Stripe PaymentMethod record
    stripe_pm, _ = PaymentMethod.objects.get_or_create(
        type='stripe',
        defaults={
            'name': 'Stripe',
            'description': 'Paiement en ligne par carte bancaire via Stripe',
            'is_active': True,
        },
    )

    # Calculate total
    total_cents = sum(
        item['amount_cents'] * item.get('quantity', 1) for item in line_items
    )
    total_amount = Decimal(str(total_cents)) / 100
    currency = line_items[0]['currency'].upper()

    # Create Transaction (pending)
    description_parts = [item['name'] for item in line_items]
    transaction = Transaction.objects.create(
        type='income',
        amount=total_amount,
        currency=currency,
        status='pending',
        description='; '.join(description_parts),
        payment_method=stripe_pm,
        created_by=request.user,
        metadata={
            'stripe_session_id': session.id,
            'checkout_type': metadata.get('type', 'unknown'),
        },
    )

    # Create PaymentAttempt (initiated)
    PaymentAttempt.objects.create(
        transaction=transaction,
        payment_method=stripe_pm,
        amount=total_amount,
        currency=currency,
        status='initiated',
        stripe_session_id=session.id,
        payer=request.user,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        provider_response={
            'session_id': session.id,
            'session_url': session.url,
        },
    )

    logger.info(
        "Stripe checkout %s created for user %s, %s %s",
        session.id, request.user.id, total_amount, currency,
    )

    # Redirect to Stripe Checkout
    return redirect(session.url)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Stripe webhook endpoint.

    CSRF exempt - Stripe cannot send CSRF tokens.
    Must receive raw request.body for signature verification.

    Register in Stripe Dashboard:
      URL: https://martialcomp.com/finances/stripe/webhook/
      Events: checkout.session.completed, checkout.session.expired,
              payment_intent.payment_failed, charge.refunded,
              customer.subscription.updated,
              customer.subscription.deleted,
              invoice.payment_succeeded, invoice.payment_failed
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    if not sig_header:
        logger.warning("stripe_webhook: Missing Stripe-Signature header")
        return HttpResponse('Missing Stripe-Signature header', status=400)

    # Parse and verify
    try:
        event = StripeService.handle_webhook(payload, sig_header)
    except StripeServiceError as e:
        logger.warning("stripe_webhook: Verification failed: %s", e)
        return HttpResponse(f'Webhook error: {e}', status=400)

    event_type = event['event_type']
    event_id = event['event_id']
    event_data = event['data']

    logger.info("Stripe webhook received: type=%s, id=%s", event_type, event_id)

    # Dispatch to business logic
    try:
        result = StripeWebhookHandler.dispatch(event_type, event_data)
        logger.info("Stripe webhook %s handled: %s", event_type, result)
    except Exception as e:
        # Log but return 200 to prevent Stripe retry loops on our bugs
        logger.exception("Error handling Stripe webhook %s: %s", event_type, e)

    return HttpResponse('OK', status=200)


@login_required
def checkout_success(request):
    """
    Success page after Stripe Checkout completes.

    The real payment update happens via webhook, not here.
    This is purely informational for the user.
    """
    session_id = request.GET.get('session_id', '')
    payment_attempt = None
    session_data = None

    if session_id:
        try:
            payment_attempt = PaymentAttempt.objects.select_related(
                'transaction'
            ).get(
                stripe_session_id=session_id,
                payer=request.user,
            )
        except PaymentAttempt.DoesNotExist:
            pass

        # Belt-and-suspenders: check Stripe directly
        try:
            stripe_session = StripeService.retrieve_session(session_id)
            session_data = {
                'payment_status': stripe_session.payment_status,
                'amount_total': stripe_session.amount_total,
                'currency': (stripe_session.currency or '').upper(),
            }
        except StripeServiceError:
            pass

    context = {
        'payment_attempt': payment_attempt,
        'session_data': session_data,
    }
    return render(request, 'finances/stripe/checkout_success.html', context)


@login_required
def checkout_cancel(request):
    """
    Cancel page when user clicks 'Back' on Stripe Checkout.
    The PaymentAttempt stays 'initiated' until session expires (webhook handles that).
    """
    return render(request, 'finances/stripe/checkout_cancel.html', {})


@login_required
@require_POST
def create_subscription_checkout(request):
    """
    Create a Stripe Checkout Session for Premium subscription upgrade.

    Flow:
    1. Get org + subscription, verify currently on Free tier
    2. Determine Price ID based on market tier (mature/emergent)
    3. Get or create Stripe Customer
    4. Create Checkout Session in subscription mode
    5. Redirect to Stripe hosted page
    """
    from apps.competitions.utils.feature_control import get_user_organization
    from apps.finances.services.subscription_service import get_subscription_info
    from apps.finances.pricing_tiers import get_market_tier_for_country, MARKET_TIER_MATURE

    organization = get_user_organization(request.user)
    if not organization:
        logger.warning("create_subscription_checkout: no organization for user %s", request.user.id)
        return redirect('upgrade_required')

    sub_info = get_subscription_info(organization)
    if not sub_info.get('is_free', True):
        # Already premium, no need to upgrade
        return redirect('dashboard:club')

    # Get the OrganizationSubscription
    from apps.competitions.utils.feature_control import get_organization_subscription
    subscription = get_organization_subscription(organization)
    if not subscription:
        logger.error("create_subscription_checkout: no subscription record for org %s", organization.pk)
        return redirect('upgrade_required')

    # Determine Price ID based on country
    country = getattr(organization, 'country', '') or ''
    market_tier = get_market_tier_for_country(country)
    if market_tier == MARKET_TIER_MATURE:
        price_id = getattr(settings, 'STRIPE_PRICE_MATURE_YEARLY', '')
    else:
        price_id = getattr(settings, 'STRIPE_PRICE_EMERGENT_YEARLY', '')

    if not price_id:
        logger.error(
            "create_subscription_checkout: no Stripe Price ID configured for %s market",
            market_tier,
        )
        return render(request, 'finances/upgrade_required.html', {
            'subscription_info': sub_info,
            'error': 'Stripe subscription not configured yet. Please contact support.',
        })

    # Get or create Stripe Customer
    org_name = getattr(organization, 'name', '') or str(organization)
    try:
        customer = StripeService.get_or_create_customer(
            email=request.user.email,
            name=org_name,
            metadata={
                'organization_id': str(organization.pk),
                'user_id': str(request.user.id),
            },
            existing_customer_id=subscription.stripe_customer_id or None,
        )
    except StripeServiceError as e:
        logger.error("create_subscription_checkout: customer creation failed: %s", e)
        return render(request, 'finances/upgrade_required.html', {
            'subscription_info': sub_info,
            'error': str(e),
        })

    # Save customer ID on subscription
    if subscription.stripe_customer_id != customer.id:
        subscription.stripe_customer_id = customer.id
        subscription.save(update_fields=['stripe_customer_id'])

    # Member count for quantity
    members_count = sub_info.get('members_count', 1)
    if members_count < 1:
        members_count = 1

    # Build URLs
    base_url = request.build_absolute_uri('/').rstrip('/')
    lang = get_language() or 'fr'
    success_url = (
        f"{base_url}/{lang}/finances/stripe/success/"
        f"?session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = f"{base_url}/upgrade/"

    # Create Checkout Session
    try:
        session = StripeService.create_checkout_session(
            line_items=[{
                'price': price_id,
                'quantity': members_count,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            customer=customer.id,
            metadata={
                'organization_id': str(organization.pk),
                'subscription_id': str(subscription.pk),
                'user_id': str(request.user.id),
                'checkout_type': 'premium_subscription',
            },
            mode='subscription',
        )
    except StripeServiceError as e:
        logger.error("create_subscription_checkout: session creation failed: %s", e)
        return render(request, 'finances/upgrade_required.html', {
            'subscription_info': sub_info,
            'error': str(e),
        })

    logger.info(
        "Subscription checkout created: session=%s, org=%s, members=%d",
        session.id, organization.pk, members_count,
    )
    return redirect(session.url)
