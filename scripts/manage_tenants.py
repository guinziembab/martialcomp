#!/usr/bin/env python
"""
MartialComp Tenant Management Script
Provides utilities for managing tenants in production
"""
import os
import sys
import argparse
import json
from datetime import datetime, timedelta

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from multitenant.models import Tenant, Domain
from multitenant.utils import create_schema_for_tenant, drop_tenant_schema
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone


class TenantManager:
    """Utility class for tenant management operations"""
    
    def list_tenants(self, active_only=True):
        """List all tenants"""
        queryset = Tenant.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        tenants = []
        for tenant in queryset:
            tenants.append({
                'id': str(tenant.id),
                'name': tenant.name,
                'slug': tenant.slug,
                'domain': tenant.domain,
                'plan': tenant.subscription_plan,
                'active': tenant.is_active,
                'trial': tenant.is_trial,
                'created': tenant.created_at.isoformat() if hasattr(tenant, 'created_at') else None,
                'owner': tenant.owner.email if tenant.owner else None,
            })
        
        print(json.dumps(tenants, indent=2))
        return tenants
    
    def create_tenant(self, name, slug, owner_email, **kwargs):
        """Create a new tenant"""
        try:
            with transaction.atomic():
                # Create or get owner
                owner, created = User.objects.get_or_create(
                    email=owner_email,
                    defaults={
                        'username': owner_email,
                        'first_name': kwargs.get('first_name', ''),
                        'last_name': kwargs.get('last_name', ''),
                    }
                )
                
                if created and kwargs.get('password'):
                    owner.set_password(kwargs['password'])
                    owner.save()
                
                # Create tenant
                tenant = Tenant.objects.create(
                    name=name,
                    slug=slug,
                    schema_name=f"tenant_{slug.replace('-', '_')}",
                    domain=f"{slug}.martialcomp.com",
                    owner=owner,
                    continent=kwargs.get('continent', 'europe_west'),
                    subscription_plan=kwargs.get('plan', 'essentials'),
                    currency=kwargs.get('currency', 'EUR'),
                    language=kwargs.get('language', 'fr'),
                    timezone=kwargs.get('timezone', 'Europe/Paris'),
                    is_active=True,
                    is_trial=kwargs.get('trial', True),
                )
                
                # Create primary domain
                Domain.objects.create(
                    tenant=tenant,
                    domain=tenant.domain,
                    is_primary=True
                )
                
                # Create custom domain if provided
                if kwargs.get('custom_domain'):
                    Domain.objects.create(
                        tenant=tenant,
                        domain=kwargs['custom_domain'],
                        is_primary=False
                    )
                
                # Create schema
                create_schema_for_tenant(tenant)
                
                print(f"✓ Tenant '{name}' created successfully")
                print(f"  ID: {tenant.id}")
                print(f"  Domain: {tenant.domain}")
                print(f"  Schema: {tenant.schema_name}")
                
        except Exception as e:
            print(f"✗ Error creating tenant: {str(e)}")
            sys.exit(1)
    
    def deactivate_tenant(self, identifier):
        """Deactivate a tenant"""
        try:
            tenant = self._get_tenant(identifier)
            tenant.is_active = False
            tenant.deactivated_at = timezone.now()
            tenant.save()
            
            print(f"✓ Tenant '{tenant.name}' deactivated")
            
        except Exception as e:
            print(f"✗ Error deactivating tenant: {str(e)}")
            sys.exit(1)
    
    def activate_tenant(self, identifier):
        """Activate a tenant"""
        try:
            tenant = self._get_tenant(identifier)
            tenant.is_active = True
            tenant.activated_at = timezone.now()
            tenant.save()
            
            print(f"✓ Tenant '{tenant.name}' activated")
            
        except Exception as e:
            print(f"✗ Error activating tenant: {str(e)}")
            sys.exit(1)
    
    def update_plan(self, identifier, new_plan):
        """Update tenant subscription plan"""
        try:
            tenant = self._get_tenant(identifier)
            old_plan = tenant.subscription_plan
            tenant.subscription_plan = new_plan
            tenant.save()
            
            print(f"✓ Tenant '{tenant.name}' plan updated")
            print(f"  Old plan: {old_plan}")
            print(f"  New plan: {new_plan}")
            print(f"  New price: {tenant.get_price_for_plan()}€/year")
            
        except Exception as e:
            print(f"✗ Error updating plan: {str(e)}")
            sys.exit(1)
    
    def extend_trial(self, identifier, days):
        """Extend tenant trial period"""
        try:
            tenant = self._get_tenant(identifier)
            
            if not tenant.is_trial:
                print(f"✗ Tenant '{tenant.name}' is not in trial")
                return
            
            if tenant.trial_end_date:
                tenant.trial_end_date += timedelta(days=days)
            else:
                tenant.trial_end_date = timezone.now() + timedelta(days=days)
            
            tenant.save()
            
            print(f"✓ Trial extended for '{tenant.name}'")
            print(f"  New trial end date: {tenant.trial_end_date.strftime('%Y-%m-%d')}")
            
        except Exception as e:
            print(f"✗ Error extending trial: {str(e)}")
            sys.exit(1)
    
    def delete_tenant(self, identifier, force=False):
        """Delete a tenant (use with caution!)"""
        try:
            tenant = self._get_tenant(identifier)
            
            if not force:
                print(f"⚠️  WARNING: This will permanently delete tenant '{tenant.name}'")
                print("  All data will be lost!")
                confirm = input("  Type 'DELETE' to confirm: ")
                
                if confirm != 'DELETE':
                    print("✗ Deletion cancelled")
                    return
            
            # Drop schema
            drop_tenant_schema(tenant, cascade=True)
            
            # Delete tenant
            tenant_name = tenant.name
            tenant.delete()
            
            print(f"✓ Tenant '{tenant_name}' deleted")
            
        except Exception as e:
            print(f"✗ Error deleting tenant: {str(e)}")
            sys.exit(1)
    
    def tenant_info(self, identifier):
        """Show detailed tenant information"""
        try:
            tenant = self._get_tenant(identifier)
            
            info = {
                'id': str(tenant.id),
                'name': tenant.name,
                'slug': tenant.slug,
                'schema_name': tenant.schema_name,
                'domain': tenant.domain,
                'domains': [d.domain for d in tenant.domains.all()],
                'owner': {
                    'email': tenant.owner.email if tenant.owner else None,
                    'name': tenant.owner.get_full_name() if tenant.owner else None,
                },
                'subscription': {
                    'plan': tenant.subscription_plan,
                    'price': f"{tenant.get_price_for_plan()}€/year",
                    'is_trial': tenant.is_trial,
                    'trial_end': tenant.trial_end_date.isoformat() if tenant.trial_end_date else None,
                },
                'location': {
                    'continent': tenant.continent,
                    'country': tenant.country,
                    'timezone': tenant.timezone,
                    'language': tenant.language,
                    'currency': tenant.currency,
                },
                'status': {
                    'is_active': tenant.is_active,
                    'created_at': tenant.created_at.isoformat() if hasattr(tenant, 'created_at') else None,
                    'activated_at': tenant.activated_at.isoformat() if hasattr(tenant, 'activated_at') else None,
                    'deactivated_at': tenant.deactivated_at.isoformat() if hasattr(tenant, 'deactivated_at') else None,
                },
                'features': tenant.get_available_features(),
                'payment_config': tenant.payment_config,
            }
            
            print(json.dumps(info, indent=2))
            
        except Exception as e:
            print(f"✗ Error getting tenant info: {str(e)}")
            sys.exit(1)
    
    def _get_tenant(self, identifier):
        """Get tenant by ID, slug, or domain"""
        try:
            # Try UUID first
            return Tenant.objects.get(id=identifier)
        except (Tenant.DoesNotExist, ValueError):
            pass
        
        try:
            # Try slug
            return Tenant.objects.get(slug=identifier)
        except Tenant.DoesNotExist:
            pass
        
        try:
            # Try domain
            return Tenant.objects.get(domain=identifier)
        except Tenant.DoesNotExist:
            pass
        
        # Try custom domain
        domain = Domain.objects.filter(domain=identifier).first()
        if domain:
            return domain.tenant
        
        raise ValueError(f"Tenant not found: {identifier}")


def main():
    parser = argparse.ArgumentParser(description='MartialComp Tenant Management')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all tenants')
    list_parser.add_argument('--all', action='store_true', help='Include inactive tenants')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new tenant')
    create_parser.add_argument('name', help='Tenant name')
    create_parser.add_argument('slug', help='URL slug')
    create_parser.add_argument('owner_email', help='Owner email')
    create_parser.add_argument('--password', help='Owner password')
    create_parser.add_argument('--first-name', help='Owner first name')
    create_parser.add_argument('--last-name', help='Owner last name')
    create_parser.add_argument('--continent', default='europe_west', help='Continent')
    create_parser.add_argument('--plan', default='essentials', help='Subscription plan')
    create_parser.add_argument('--custom-domain', help='Custom domain')
    create_parser.add_argument('--no-trial', action='store_false', dest='trial', help='Skip trial period')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show tenant information')
    info_parser.add_argument('tenant', help='Tenant ID, slug, or domain')
    
    # Deactivate command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a tenant')
    deactivate_parser.add_argument('tenant', help='Tenant ID, slug, or domain')
    
    # Activate command
    activate_parser = subparsers.add_parser('activate', help='Activate a tenant')
    activate_parser.add_argument('tenant', help='Tenant ID, slug, or domain')
    
    # Update plan command
    plan_parser = subparsers.add_parser('update-plan', help='Update subscription plan')
    plan_parser.add_argument('tenant', help='Tenant ID, slug, or domain')
    plan_parser.add_argument('plan', choices=['essentials', 'masters', 'champion'], help='New plan')
    
    # Extend trial command
    trial_parser = subparsers.add_parser('extend-trial', help='Extend trial period')
    trial_parser.add_argument('tenant', help='Tenant ID, slug, or domain')
    trial_parser.add_argument('days', type=int, help='Days to extend')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a tenant')
    delete_parser.add_argument('tenant', help='Tenant ID, slug, or domain')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = TenantManager()
    
    if args.command == 'list':
        manager.list_tenants(active_only=not args.all)
    
    elif args.command == 'create':
        manager.create_tenant(
            name=args.name,
            slug=args.slug,
            owner_email=args.owner_email,
            password=args.password,
            first_name=args.first_name,
            last_name=args.last_name,
            continent=args.continent,
            plan=args.plan,
            custom_domain=args.custom_domain,
            trial=args.trial,
        )
    
    elif args.command == 'info':
        manager.tenant_info(args.tenant)
    
    elif args.command == 'deactivate':
        manager.deactivate_tenant(args.tenant)
    
    elif args.command == 'activate':
        manager.activate_tenant(args.tenant)
    
    elif args.command == 'update-plan':
        manager.update_plan(args.tenant, args.plan)
    
    elif args.command == 'extend-trial':
        manager.extend_trial(args.tenant, args.days)
    
    elif args.command == 'delete':
        manager.delete_tenant(args.tenant, force=args.force)


if __name__ == '__main__':
    main()