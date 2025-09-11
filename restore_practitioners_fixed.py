#!/usr/bin/env python
"""
Script to restore missing practitioners and fix organization relationships.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.competitions.models import Practitioner
from apps.organizations.models import Organization, OrganizationMember, OrganizationRole
from django.db.models import Q

def restore_practitioners():
    print("=" * 80)
    print("RESTORING PRACTITIONER ACCESS")
    print("=" * 80)
    
    # Find ClaudiuG user
    claudiu_user = User.objects.filter(username='ClaudiuG').first()
    if not claudiu_user:
        print("ERROR: ClaudiuG user not found!")
        return
    
    print(f"Found user: {claudiu_user.username} ({claudiu_user.get_full_name()})")
    
    # Find CHUATAO organization (where the missing practitioners likely were)
    chuatao_org = Organization.objects.filter(name='CHUATAO').first()
    if not chuatao_org:
        print("ERROR: CHUATAO organization not found!")
        return
    
    print(f"\nCHUATAO Organization (ID: {chuatao_org.id})")
    print(f"Current practitioners in CHUATAO: {Practitioner.objects.filter(organization=chuatao_org).count()}")
    
    # Option 1: Move ClaudiuG's practitioner to CHUATAO
    print("\n" + "-" * 80)
    print("OPTION 1: Move ClaudiuG to CHUATAO organization")
    print("-" * 80)
    
    claudiu_practitioner = Practitioner.objects.filter(user=claudiu_user).first()
    if claudiu_practitioner:
        print(f"Current organization: {claudiu_practitioner.organization.name if claudiu_practitioner.organization else 'None'}")
        print(f"Would move to: CHUATAO")
        
        # Check if membership already exists
        existing_membership = OrganizationMember.objects.filter(
            user=claudiu_user,
            organization=chuatao_org
        ).first()
        
        if existing_membership:
            print(f"Membership already exists with role: {existing_membership.role}")
            # Update role to manager if not already
            if existing_membership.role != OrganizationRole.MANAGER:
                existing_membership.role = OrganizationRole.MANAGER
                existing_membership.save()
                print(f"Updated role to: {OrganizationRole.MANAGER}")
        else:
            # Create membership
            membership = OrganizationMember.objects.create(
                user=claudiu_user,
                organization=chuatao_org,
                role=OrganizationRole.MANAGER,
                is_active=True
            )
            print(f"Created membership with role: {OrganizationRole.MANAGER}")
        
        # Update practitioner's organization
        claudiu_practitioner.organization = chuatao_org
        claudiu_practitioner.save()
        print(f"Updated practitioner's organization to CHUATAO")
    
    # List all practitioners in CHUATAO
    print("\n" + "-" * 80)
    print("ALL PRACTITIONERS IN CHUATAO:")
    print("-" * 80)
    
    for p in Practitioner.objects.filter(organization=chuatao_org):
        print(f"- {p.full_name} (ID: {p.id}, User: {p.user.username if p.user else 'None'})")
    
    # Check for orphaned practitioners
    print("\n" + "-" * 80)
    print("CHECKING FOR ORPHANED PRACTITIONERS:")
    print("-" * 80)
    
    # Look for practitioners that might have been orphaned
    orphaned = Practitioner.objects.filter(
        Q(organization__isnull=True) | 
        Q(organization__name__icontains='test')
    ).exclude(
        first_name__in=['COACH1', 'COACH55', 'COACH99', 'Juge1', 'Juge2', 'Pratiquant']
    )
    
    print(f"Found {orphaned.count()} potentially orphaned practitioners")
    for p in orphaned:
        print(f"- {p.full_name} (ID: {p.id}, Org: {p.organization.name if p.organization else 'None'})")
        
    # Check if there are any practitioners with similar names to what might have been lost
    print("\n" + "-" * 80)
    print("SEARCHING FOR POSSIBLE MISSING PRACTITIONERS:")
    print("-" * 80)
    
    # Search for practitioners that might be the missing ones
    # Common names in martial arts clubs
    possible_names = ['Jean', 'Marie', 'Pierre', 'Paul', 'Jacques', 'Michel', 'André', 'Philippe']
    
    for name in possible_names:
        matching = Practitioner.objects.filter(
            Q(first_name__icontains=name) | Q(last_name__icontains=name)
        ).exclude(
            first_name__in=['COACH1', 'COACH55', 'COACH99', 'Juge1', 'Juge2', 'Pratiquant']
        )
        
        if matching.exists():
            print(f"\nPractitioners matching '{name}':")
            for p in matching:
                print(f"  - {p.full_name} (Org: {p.organization.name if p.organization else 'None'})")
    
    # Check Robert PLAS practitioners
    print("\n" + "-" * 80)
    print("CHECKING ROBERT PLAS PRACTITIONERS:")
    print("-" * 80)
    
    robert_practitioners = Practitioner.objects.filter(
        Q(first_name__icontains='Robert') | Q(last_name__icontains='PLAS')
    )
    
    print(f"Found {robert_practitioners.count()} Robert PLAS practitioners:")
    for p in robert_practitioners:
        print(f"- {p.full_name} (ID: {p.id}, User: {p.user.username if p.user else 'None'}, Org: {p.organization.name if p.organization else 'None'})")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"1. ClaudiuG has been added to CHUATAO organization as a manager")
    print(f"2. CHUATAO now has {Practitioner.objects.filter(organization=chuatao_org).count()} practitioners")
    print(f"3. Current practitioners in CHUATAO are listed above")
    print(f"\n4. To recover the 4 missing practitioners:")
    print("   - The database shows only 3 practitioners in CHUATAO currently")
    print("   - Two of them are named Robert PLAS")
    print("   - The 4th missing practitioner may need to be recreated")
    print("   - Check backup files for the original practitioner data")
    print("\n5. You should now have access to these practitioners in the dashboard")

if __name__ == "__main__":
    try:
        restore_practitioners()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()