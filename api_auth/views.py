from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
import uuid
import datetime
import secrets
import string

from django.db import IntegrityError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import RefreshToken, DeviceRegistration, PKCESession, AccessTokenLog, SSOToken
from .serializers import (
    LoginSerializer, RegistrationSerializer, TokenSerializer, UserSerializer,
    RefreshTokenSerializer, DeviceRegistrationSerializer, LogoutSerializer,
    PKCEInitSerializer, PKCECompleteSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

User = get_user_model()


class LoginView(APIView):
    """
    Vue pour l'authentification des utilisateurs et la génération de tokens JWT
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Récupération de l'utilisateur et des données d'appareil
            user = serializer.validated_data['user']
            device_id = serializer.validated_data.get('device_id')
            device_name = serializer.validated_data.get('device_name')
            device_model = serializer.validated_data.get('device_model')
            os_version = serializer.validated_data.get('os_version')
            app_version = serializer.validated_data.get('app_version')
            
            # PKCE parameters
            code_challenge = serializer.validated_data.get('code_challenge')
            code_challenge_method = serializer.validated_data.get('code_challenge_method', 'S256')
            
            # Multi-tenant context
            tenant = getattr(request, 'tenant', None)
            
            # Génération des tokens JWT
            jwt_refresh = JWTRefreshToken.for_user(user)
            
            # Ajouter des claims personnalisés au token JWT
            if tenant:
                jwt_refresh['tenant_id'] = str(tenant.id)
                jwt_refresh['tenant_name'] = tenant.name
            
            # Définis le JTI pour le token d'accès pour les logs
            jti = str(uuid.uuid4())
            jwt_refresh.access_token['jti'] = jti
            
            # Si un appareil est spécifié, l'enregistrer
            if device_id:
                device, created = DeviceRegistration.objects.get_or_create(
                    user=user,
                    device_id=device_id,
                    defaults={
                        'device_name': device_name,
                        'device_model': device_model,
                        'os_version': os_version,
                        'app_version': app_version,
                        'tenant': tenant
                    }
                )
                
                # Si l'appareil existe, mettre à jour ses informations
                if not created:
                    if device_name:
                        device.device_name = device_name
                    if device_model:
                        device.device_model = device_model
                    if os_version:
                        device.os_version = os_version
                    if app_version:
                        device.app_version = app_version
                    device.last_used_at = timezone.now()
                    device.save()
            
            # Créer un RefreshToken dans la base de données
            # Calculer la date d'expiration (par défaut 30 jours)
            expires_in_days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
            expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
            
            # Créer un token de rafraîchissement en base de données
            db_refresh_token = RefreshToken.objects.create(
                user=user,
                token=str(jwt_refresh),
                expires_at=expires_at,
                device_id=device_id,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method if code_challenge else None,
            )
            
            # Enregistrer le jeton d'accès dans les logs
            access_token_expires = timezone.now() + datetime.timedelta(minutes=60)  # 1 heure par défaut
            
            AccessTokenLog.objects.create(
                user=user,
                jti=jti,
                expires_at=access_token_expires,
                device_id=device_id,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Préparer la réponse
            response_data = {
                'access': str(jwt_refresh.access_token),
                'refresh': str(jwt_refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 heure pour le token d'accès
            }
            
            return Response(TokenSerializer(response_data).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RegisterView(APIView):
    """
    Vue pour l'inscription de nouveaux utilisateurs
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
            except IntegrityError as e:
                # Gérer les erreurs de contrainte unique (race condition)
                error_msg = str(e).lower()
                if 'username' in error_msg:
                    return Response(
                        {'username': [_("Ce nom d'utilisateur est déjà utilisé.")]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif 'email' in error_msg:
                    return Response(
                        {'email': [_("Cette adresse email est déjà utilisée.")]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {'detail': _("Une erreur est survenue lors de l'inscription.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Récupération des informations d'appareil
            device_data = {
                'device_id': request.data.get('device_id'),
                'device_name': request.data.get('device_name'),
                'device_model': request.data.get('device_model'),
                'os_version': request.data.get('os_version'),
                'app_version': request.data.get('app_version'),
            }
            
            # Si un ID d'appareil est fourni, l'enregistrer
            if device_data['device_id']:
                DeviceRegistration.objects.create(
                    user=user,
                    **{k: v for k, v in device_data.items() if v is not None},
                    tenant=getattr(request, 'tenant', None)
                )
            
            # Générer des tokens pour le nouvel utilisateur
            jwt_refresh = JWTRefreshToken.for_user(user)
            
            # Multi-tenant context
            tenant = getattr(request, 'tenant', None)
            if tenant:
                jwt_refresh['tenant_id'] = str(tenant.id)
                jwt_refresh['tenant_name'] = tenant.name
            
            # Définis le JTI pour le token d'accès pour les logs
            jti = str(uuid.uuid4())
            jwt_refresh.access_token['jti'] = jti
            
            # Créer un RefreshToken dans la base de données
            expires_in_days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
            expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
            
            RefreshToken.objects.create(
                user=user,
                token=str(jwt_refresh),
                expires_at=expires_at,
                device_id=device_data.get('device_id'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Enregistrer le jeton d'accès dans les logs
            access_token_expires = timezone.now() + datetime.timedelta(minutes=60)  # 1 heure par défaut
            
            AccessTokenLog.objects.create(
                user=user,
                jti=jti,
                expires_at=access_token_expires,
                device_id=device_data.get('device_id'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Préparer la réponse
            response_data = {
                'access': str(jwt_refresh.access_token),
                'refresh': str(jwt_refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 heure pour le token d'accès
            }
            
            return Response(TokenSerializer(response_data).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RefreshTokenView(APIView):
    """
    Vue pour rafraîchir les tokens d'accès
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if serializer.is_valid():
            # Récupérer les objets validés
            db_token = serializer.validated_data['token_obj']
            user = serializer.validated_data['user']
            
            # Générer un nouveau token JWT
            jwt_refresh = JWTRefreshToken.for_user(user)
            
            # Multi-tenant context
            tenant = getattr(request, 'tenant', None) or db_token.tenant
            if tenant:
                jwt_refresh['tenant_id'] = str(tenant.id)
                jwt_refresh['tenant_name'] = tenant.name
            
            # Définis le JTI pour le token d'accès pour les logs
            jti = str(uuid.uuid4())
            jwt_refresh.access_token['jti'] = jti
            
            # Révoquer l'ancien token de rafraîchissement
            db_token.revoked = True
            db_token.save(update_fields=['revoked'])
            
            # Créer un nouveau token de rafraîchissement en base de données
            expires_in_days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
            expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
            
            new_db_token = RefreshToken.objects.create(
                user=user,
                token=str(jwt_refresh),
                expires_at=expires_at,
                device_id=db_token.device_id,
                user_agent=request.META.get('HTTP_USER_AGENT', '') or db_token.user_agent,
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Enregistrer le jeton d'accès dans les logs
            access_token_expires = timezone.now() + datetime.timedelta(minutes=60)  # 1 heure par défaut
            
            AccessTokenLog.objects.create(
                user=user,
                jti=jti,
                expires_at=access_token_expires,
                device_id=db_token.device_id,
                user_agent=request.META.get('HTTP_USER_AGENT', '') or db_token.user_agent,
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Préparer la réponse
            response_data = {
                'access': str(jwt_refresh.access_token),
                'refresh': str(jwt_refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 heure pour le token d'accès
            }
            
            return Response(TokenSerializer(response_data).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    Vue pour la déconnexion et la révocation des tokens
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            # Si un token a été trouvé, le révoquer
            token_obj = serializer.validated_data.get('token_obj')
            if token_obj:
                token_obj.revoked = True
                token_obj.save(update_fields=['revoked'])
                
                # Révoquer aussi toutes les sessions PKCE associées
                PKCESession.objects.filter(
                    user=token_obj.user, 
                    used=False
                ).update(used=True)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    """
    Vue pour obtenir les informations de l'utilisateur connecté
    Inclut le rôle et les permissions pour l'application mobile
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        data = serializer.data

        # Get user profile to determine role
        try:
            from apps.competitions.models import UserProfile
            profile = UserProfile.objects.filter(user=user).first()
        except Exception:
            profile = None

        # Determine user role
        user_role = getattr(profile, 'role', 'participant') if profile else 'participant'

        # Build permissions list based on role
        user_permissions = []
        if user_role == 'federation_admin':
            user_permissions = ['manage_clubs', 'manage_competitions', 'manage_judges', 'view_statistics', 'manage_grades']
        elif user_role == 'club_manager':
            user_permissions = ['manage_practitioners', 'manage_registrations', 'manage_competitions', 'view_statistics']
        elif user_role == 'coach':
            user_permissions = ['view_practitioners', 'manage_training', 'view_statistics']
        elif user_role == 'judge':
            user_permissions = ['judge_competitions', 'view_assignments']
        else:  # participant or default
            user_permissions = ['view_competitions', 'register_competitions', 'view_grades']

        # Check if user is also a judge (dual role) - check multiple paths
        is_also_judge = False
        try:
            from apps.competitions.models import Judge
            from apps.competitions.models import Practitioner

            # Method 1: Direct user link
            judge_exists = Judge.objects.filter(user=user, active=True).exists()

            # Method 2: Via practitioner
            if not judge_exists:
                practitioner = Practitioner.objects.filter(user=user).first()
                if practitioner:
                    judge_exists = Judge.objects.filter(practitioner=practitioner, active=True).exists()

            # Method 3: Check AdHocJudge
            if not judge_exists:
                try:
                    from apps.competitions.models.adhoc_judges import AdHocJudge
                    practitioner = Practitioner.objects.filter(user=user).first()
                    if practitioner:
                        adhoc = AdHocJudge.get_active_for_practitioner(practitioner)
                        judge_exists = adhoc.exists()
                except Exception:
                    pass

            is_also_judge = judge_exists
            if is_also_judge and 'judge_competitions' not in user_permissions:
                user_permissions.append('judge_competitions')
                user_permissions.append('view_assignments')
        except Exception:
            pass

        # Get avatar_url from practitioner linked to user
        avatar_url = None
        try:
            from apps.competitions.models import Practitioner
            practitioner = Practitioner.objects.filter(user=user).first()
            if practitioner and practitioner.photo:
                photo_url = practitioner.photo.url
                avatar_url = request.build_absolute_uri(photo_url)
                # Ensure HTTPS in production
                if 'martialcomp.com' in avatar_url and avatar_url.startswith('http://'):
                    avatar_url = avatar_url.replace('http://', 'https://')
        except Exception:
            pass

        # Add role, permissions, and avatar_url to response
        data['role'] = user_role
        data['permissions'] = user_permissions
        data['is_also_judge'] = is_also_judge
        data['avatar_url'] = avatar_url

        return Response(data)


class UserProfileView(APIView):
    """Profil enrichi pour l'application mobile."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        # PRIORITY: Try via X-Tenant-ID header (sent by mobile app)
        organization = None
        tenant_id = request.META.get('HTTP_X_TENANT_ID') or request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                from apps.organizations.models import Organization
                org_by_tenant = Organization.objects.filter(id=tenant_id).first()
                if org_by_tenant:
                    organization = org_by_tenant
                    print(f"DEBUG UserProfileView: Found organization via X-Tenant-ID header: {organization.name} (id={organization.id})")
            except Exception as e:
                print(f"DEBUG UserProfileView: Error getting organization from X-Tenant-ID: {e}")

        # Always get UserProfile for user data (role, join_date, etc.)
        profile = None
        try:
            from apps.competitions.models import UserProfile
            profile = UserProfile.objects.filter(user=user).select_related('organization').first()
        except Exception as e:
            print(f"DEBUG UserProfileView: Error getting UserProfile: {e}")

        # Fallback: Get organization from UserProfile if not found via X-Tenant-ID
        if not organization:
            if profile and profile.organization:
                organization = profile.organization
                print(f"DEBUG UserProfileView: Found organization via UserProfile: {organization.name} (id={organization.id})")

        # Fallback methods if UserProfile doesn't have organization
        if not organization:
            organization = getattr(user, 'organization', None)
            if organization:
                print(f"DEBUG UserProfileView: Found organization via user.organization")

        if not organization:
            try:
                from apps.organizations.models import OrganizationMember
                membership = OrganizationMember.objects.filter(user=user, is_active=True).select_related('organization').first()
                if membership and membership.organization:
                    organization = membership.organization
                    print(f"DEBUG UserProfileView: Found organization via OrganizationMember: {organization.name}")
            except Exception as e:
                print(f"DEBUG UserProfileView: Error getting OrganizationMember: {e}")

        # Get statistics
        practitioners_count = 0
        active_registrations = 0
        organized_competitions = 0
        judges_referees = 0

        if organization:
            org_id = organization.id
            try:
                from apps.competitions.models import Practitioner, Competition, Judge
                from django.db.models import Q

                practitioners_count = Practitioner.objects.filter(organization_id=org_id).count()
                organized_competitions = Competition.objects.filter(organizing_organization_id=org_id).count()

                try:
                    from apps.competitions.models.registrations import CompetitionRegistration
                    active_registrations = CompetitionRegistration.objects.filter(
                        Q(competition__organizing_organization_id=org_id) | Q(practitioner__organization_id=org_id),
                        status__in=['pending', 'confirmed', 'validated', 'registered']
                    ).count()
                except Exception:
                    pass

                try:
                    judges_referees = Judge.objects.filter(
                        Q(practitioner__organization_id=org_id) | Q(organization_id=org_id),
                        active=True
                    ).count()
                except Exception:
                    pass

                print(f"DEBUG UserProfileView: Stats - practitioners={practitioners_count}, competitions={organized_competitions}, registrations={active_registrations}, judges={judges_referees}")
            except Exception as e:
                print(f"DEBUG UserProfileView: Error getting statistics: {e}")

        # Get practitioner linked to user for disciplines, grades, etc.
        practitioner = None
        disciplines_data = []
        medical_certificate_data = None
        achievements_data = []
        license_number = None
        date_of_birth = None
        phone_number = None

        try:
            from apps.competitions.models import Practitioner
            practitioner = Practitioner.objects.filter(user=user).first()
            if practitioner:
                license_number = getattr(practitioner, 'license_number', None)
                date_of_birth = getattr(practitioner, 'birth_date', None)
                phone_number = getattr(practitioner, 'phone', None) or getattr(practitioner, 'phone_number', None)
                # Debug photo
                print(f"DEBUG UserProfileView: Practitioner {practitioner.id} photo field: {practitioner.photo}")
                if practitioner.photo:
                    print(f"DEBUG UserProfileView: Photo URL: {practitioner.photo.url}")
        except Exception as e:
            print(f"DEBUG UserProfileView: Error getting practitioner: {e}")

        # Get disciplines and grades
        if practitioner:
            try:
                from apps.grades.models import PractitionerGrade
                practitioner_grades = PractitionerGrade.objects.filter(
                    practitioner=practitioner
                ).select_related('grade', 'grade__discipline').order_by('-date_obtained')

                disciplines_map = {}
                for pg in practitioner_grades:
                    if pg.grade and pg.grade.discipline:
                        disc = pg.grade.discipline
                        if disc.id not in disciplines_map:
                            disciplines_map[disc.id] = {
                                'id': disc.id,
                                'name': disc.name,
                                'grade': {
                                    'id': pg.grade.id,
                                    'name': pg.grade.name,
                                    'level': pg.grade.level,
                                    'color': getattr(pg.grade, 'color', '#000000'),
                                    'date_obtained': pg.date_obtained.isoformat() if pg.date_obtained else None,
                                    'issuing_authority': getattr(pg, 'issuing_authority', None),
                                },
                            }
                disciplines_data = list(disciplines_map.values())
            except Exception as e:
                print(f"DEBUG UserProfileView: Error getting disciplines/grades: {e}")

        # Get medical certificate
        if practitioner:
            try:
                from apps.competitions.models import MedicalCertificate
                from django.utils import timezone
                medical = MedicalCertificate.objects.filter(practitioner=practitioner).order_by('-expiry_date').first()
                if medical:
                    is_valid = medical.expiry_date and medical.expiry_date >= timezone.now().date() if hasattr(medical.expiry_date, 'date') else (medical.expiry_date >= timezone.now().date() if medical.expiry_date else False)
                    medical_certificate_data = {
                        'id': medical.id,
                        'issuance_date': medical.issue_date.isoformat() if hasattr(medical, 'issue_date') and medical.issue_date else None,
                        'expiry_date': medical.expiry_date.isoformat() if medical.expiry_date else None,
                        'is_valid': is_valid,
                        'document_url': getattr(medical, 'document', None).url if hasattr(medical, 'document') and medical.document else None,
                    }
            except Exception as e:
                print(f"DEBUG UserProfileView: Error getting medical certificate: {e}")

        # Get achievements (palmarès)
        if practitioner:
            # Method 1: Try CompetitionResult model
            try:
                from apps.competitions.models.scoring_results import CompetitionResult
                results = CompetitionResult.objects.filter(
                    practitioner=practitioner
                ).select_related('competition', 'category').order_by('-competition__start_date')[:10]
                for r in results:
                    achievements_data.append({
                        'id': r.id,
                        'title': f"{r.rank}{'er' if r.rank == 1 else 'ème'} place" if r.rank else 'Participation',
                        'description': getattr(r.category, 'name', '') if r.category else '',
                        'date': r.competition.start_date.isoformat() if r.competition and r.competition.start_date else None,
                        'category': getattr(r.category, 'name', ''),
                        'place': r.rank,
                        'competition_name': r.competition.name if r.competition else '',
                        'competitionName': r.competition.name if r.competition else '',
                    })
            except Exception as e:
                print(f"DEBUG UserProfileView: Error getting achievements from CompetitionResult: {e}")

            # Method 2: Try CompetitionRegistration if no results found
            if not achievements_data:
                try:
                    from apps.competitions.models.registrations import CompetitionRegistration
                    registrations = CompetitionRegistration.objects.filter(
                        practitioner=practitioner,
                        status__in=['completed', 'validated', 'finished']
                    ).select_related('competition', 'category').order_by('-competition__start_date')[:10]

                    for reg in registrations:
                        place = getattr(reg, 'place', None) or getattr(reg, 'ranking', None) or getattr(reg, 'final_rank', None)
                        if place and place <= 5:  # Top 5 only
                            achievements_data.append({
                                'id': reg.id,
                                'title': f"{place}{'er' if place == 1 else 'ème'} place",
                                'description': reg.category.name if reg.category else '',
                                'date': reg.competition.start_date.isoformat() if reg.competition and reg.competition.start_date else None,
                                'category': reg.category.name if reg.category else '',
                                'place': place,
                                'competition_name': reg.competition.name if reg.competition else '',
                                'competitionName': reg.competition.name if reg.competition else '',
                            })
                except Exception as e:
                    print(f"DEBUG UserProfileView: Error getting achievements from CompetitionRegistration: {e}")

        # Build club data
        club_data = None
        if organization:
            club_data = {
                'id': str(organization.id),
                'name': organization.name,
                'logo_url': getattr(organization, 'logo', None).url if hasattr(organization, 'logo') and organization.logo else None,
                'role': getattr(profile, 'role', None) if profile else None,
                'join_date': getattr(profile, 'created_at', None).isoformat() if profile and hasattr(profile, 'created_at') and profile.created_at else None,
            }

        # Determine user role and permissions
        user_role = getattr(profile, 'role', 'participant') if profile else 'participant'

        # Build permissions list based on role
        user_permissions = []
        if user_role == 'federation_admin':
            user_permissions = ['manage_clubs', 'manage_competitions', 'manage_judges', 'view_statistics', 'manage_grades']
        elif user_role == 'club_manager':
            user_permissions = ['manage_practitioners', 'manage_registrations', 'manage_competitions', 'view_statistics']
        elif user_role == 'coach':
            user_permissions = ['view_practitioners', 'manage_training', 'view_statistics']
        elif user_role == 'judge':
            user_permissions = ['judge_competitions', 'view_assignments']
        else:  # participant
            user_permissions = ['view_competitions', 'register_competitions', 'view_grades']

        # Check if user is also a judge (dual role) - check multiple paths
        is_also_judge = False
        try:
            from apps.competitions.models import Judge

            # Method 1: Direct user link
            judge_exists = Judge.objects.filter(user=user, active=True).exists()

            # Method 2: Via practitioner (already loaded above)
            if not judge_exists and practitioner:
                judge_exists = Judge.objects.filter(practitioner=practitioner, active=True).exists()

            # Method 3: Check AdHocJudge
            if not judge_exists and practitioner:
                try:
                    from apps.competitions.models.adhoc_judges import AdHocJudge
                    adhoc = AdHocJudge.get_active_for_practitioner(practitioner)
                    judge_exists = adhoc.exists()
                except Exception:
                    pass

            is_also_judge = judge_exists
            if is_also_judge and 'judge_competitions' not in user_permissions:
                user_permissions.append('judge_competitions')
                user_permissions.append('view_assignments')
        except Exception:
            pass

        # Pre-compute avatar URL once for efficiency
        avatar_url = self._get_avatar_url(request, practitioner)

        payload = {
            'user': {
                'id': user.id,
                'username': getattr(user, 'username', ''),
                'email': getattr(user, 'email', ''),
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'full_name': f"{getattr(user,'first_name','')} {getattr(user,'last_name','')}".strip(),
                'date_of_birth': date_of_birth.isoformat() if date_of_birth else None,
                'phone_number': phone_number,
                'license_number': license_number,
                'avatar_url': avatar_url,
                'role': user_role,
                'permissions': user_permissions,
                'is_also_judge': is_also_judge,
                'organization': {
                    'id': str(getattr(organization, 'id', '')),
                    'name': getattr(organization, 'name', None),
                    'slug': getattr(organization, 'slug', None),
                    'type': getattr(organization, 'organization_type', None),
                } if organization else None,
            },
            # Expose top-level data for mobile convenience (avatar_url at root level too)
            'avatar_url': avatar_url,
            'organization': {
                'id': str(getattr(organization, 'id', '')),
                'name': getattr(organization, 'name', None),
                'slug': getattr(organization, 'slug', None),
                'type': getattr(organization, 'organization_type', None),
            } if organization else None,
            'club': club_data,
            'disciplines': disciplines_data,
            'medical_certificate': medical_certificate_data,
            'achievements': achievements_data,
            'statistics': self._build_statistics(
                user, practitioner, organization,
                practitioners_count, active_registrations,
                organized_competitions, judges_referees
            ),
            'modules': {
                'finances': {'total_balance': 0, 'revenue': 0, 'expenses': 0},
                'payments': {'recent_count': 0},
                'orders': {'total': 0, 'pending': 0, 'in_progress': 0},
            }
        }
        return Response(payload)

    def _get_avatar_url(self, request, practitioner):
        """Build avatar URL with proper domain handling."""
        photo_url = None
        user = request.user

        # Try to get photo from practitioner
        if practitioner:
            if hasattr(practitioner, 'photo') and practitioner.photo:
                try:
                    photo_url = practitioner.photo.url
                    print(f"DEBUG _get_avatar_url: Got photo from practitioner.photo: {photo_url}")
                except Exception as e:
                    print(f"DEBUG _get_avatar_url: Error getting practitioner.photo: {e}")

            # Try alternative photo fields
            if not photo_url and hasattr(practitioner, 'profile_picture') and practitioner.profile_picture:
                try:
                    photo_url = practitioner.profile_picture.url
                    print(f"DEBUG _get_avatar_url: Got photo from practitioner.profile_picture: {photo_url}")
                except Exception:
                    pass

            if not photo_url and hasattr(practitioner, 'avatar') and practitioner.avatar:
                try:
                    photo_url = practitioner.avatar.url
                    print(f"DEBUG _get_avatar_url: Got photo from practitioner.avatar: {photo_url}")
                except Exception:
                    pass

        # Fallback: try to get avatar from UserProfile (which now has avatar property)
        if not photo_url and user:
            try:
                profile = getattr(user, 'profile', None)
                if profile and hasattr(profile, 'avatar') and profile.avatar:
                    photo_url = profile.avatar.url
                    print(f"DEBUG _get_avatar_url: Got photo from UserProfile.avatar: {photo_url}")
            except Exception as e:
                print(f"DEBUG _get_avatar_url: Error getting UserProfile.avatar: {e}")

        if not photo_url:
            print(f"DEBUG _get_avatar_url: No photo found for practitioner {practitioner.id if practitioner else 'None'}")
            return None

        try:
            print(f"DEBUG _get_avatar_url: Raw photo URL: {photo_url}")

            # Build absolute URL
            absolute_url = request.build_absolute_uri(photo_url)
            print(f"DEBUG _get_avatar_url: Absolute URL: {absolute_url}")

            # In production, make sure we use HTTPS
            if 'martialcomp.com' in absolute_url and absolute_url.startswith('http://'):
                absolute_url = absolute_url.replace('http://', 'https://')
                print(f"DEBUG _get_avatar_url: HTTPS URL: {absolute_url}")

            return absolute_url
        except Exception as e:
            print(f"DEBUG _get_avatar_url: Error building URL: {e}")
            return None

    def _build_statistics(self, user, practitioner, organization, practitioners_count, active_registrations, organized_competitions, judges_referees):
        """Build statistics based on user role."""
        stats = {
            'practitioners_count': practitioners_count,
            'active_registrations': active_registrations,
            'organized_competitions': organized_competitions,
            'judges_referees': judges_referees,
        }

        # Add practitioner-specific stats (combat stats, training attendance)
        if practitioner:
            # Combat statistics
            combat_stats = self._get_combat_stats(practitioner)
            stats.update({
                'total_combats': combat_stats.get('total_combats', 0),
                'victories': combat_stats.get('victories', 0),
                'defeats': combat_stats.get('defeats', 0),
                'draws': combat_stats.get('draws', 0),
                'win_rate': combat_stats.get('win_rate', 0),
                'points_scored': combat_stats.get('points_scored', 0),
                'points_conceded': combat_stats.get('points_conceded', 0),
            })

            # Training attendance
            training_stats = self._get_training_stats(practitioner)
            stats.update({
                'training_attendance': training_stats.get('attended', 0),
                'training_total': training_stats.get('total', 0),
                'training_rate': training_stats.get('rate', 0),
            })

            # Upcoming competitions count
            stats['upcoming_competitions'] = self._count_upcoming_competitions(practitioner)

            # Medals count
            stats['medals'] = self._count_medals(practitioner)

            # Pending payments/notifications
            stats['pending_payments'] = 0  # TODO: implement if needed
            stats['active_orders'] = 0  # TODO: implement if needed
            stats['unread_notifications'] = self._count_unread_notifications(user)
            stats['open_tickets'] = 0  # TODO: implement if needed

        return stats

    def _get_combat_stats(self, practitioner):
        """Get combat statistics for practitioner."""
        stats = {
            'total_combats': 0,
            'victories': 0,
            'defeats': 0,
            'draws': 0,
            'win_rate': 0,
            'points_scored': 0,
            'points_conceded': 0,
        }
        try:
            from apps.competitions.models import Combat
            from django.db.models import Q, Sum

            combats = Combat.objects.filter(
                Q(participant1__user=practitioner.user) | Q(participant2__user=practitioner.user),
                status='completed'
            ).select_related('participant1', 'participant2', 'winner')

            stats['total_combats'] = combats.count()

            for combat in combats:
                is_p1 = combat.participant1 and combat.participant1.user == practitioner.user
                is_winner = combat.winner and combat.winner.user == practitioner.user
                is_draw = combat.winner is None

                if is_winner:
                    stats['victories'] += 1
                elif is_draw:
                    stats['draws'] += 1
                else:
                    stats['defeats'] += 1

                # Points
                my_score = combat.score1 if is_p1 else combat.score2
                opp_score = combat.score2 if is_p1 else combat.score1
                stats['points_scored'] += my_score or 0
                stats['points_conceded'] += opp_score or 0

            if stats['total_combats'] > 0:
                stats['win_rate'] = round((stats['victories'] / stats['total_combats']) * 100, 1)

        except Exception as e:
            print(f"Error getting combat stats: {e}")

        return stats

    def _get_training_stats(self, practitioner):
        """Get training attendance statistics."""
        stats = {'attended': 0, 'total': 0, 'rate': 0}
        try:
            from apps.competitions.models import EventParticipant
            from django.db.models import Q
            from django.utils import timezone
            from datetime import timedelta

            # Count trainings in last 3 months
            three_months_ago = timezone.now() - timedelta(days=90)

            attendances = EventParticipant.objects.filter(
                practitioner=practitioner,
                event__event_type__in=['training', 'class', 'session', 'cours'],
                event__start_date__gte=three_months_ago.date()
            )

            stats['total'] = attendances.count()
            stats['attended'] = attendances.filter(
                Q(status='present') | Q(status='attended') | Q(attended=True)
            ).count()

            if stats['total'] > 0:
                stats['rate'] = round((stats['attended'] / stats['total']) * 100)

        except Exception as e:
            print(f"Error getting training stats: {e}")

        return stats

    def _count_upcoming_competitions(self, practitioner):
        """Count upcoming competitions with registrations."""
        try:
            from apps.competitions.models.registrations import CompetitionRegistration
            from django.utils import timezone

            return CompetitionRegistration.objects.filter(
                practitioner=practitioner,
                competition__start_date__gte=timezone.now().date(),
                status__in=['pending', 'confirmed', 'validated', 'registered']
            ).count()
        except Exception:
            return 0

    def _count_medals(self, practitioner):
        """Count medals (podium finishes)."""
        try:
            from apps.competitions.models.scoring_results import CompetitionResult

            return CompetitionResult.objects.filter(
                practitioner=practitioner,
                rank__in=[1, 2, 3]
            ).count()
        except Exception:
            return 0

    def _count_unread_notifications(self, user):
        """Count unread notifications."""
        try:
            from apps.competitions.models.notifications import Notification
            return Notification.objects.filter(user=user, is_read=False).count()
        except Exception:
            return 0

    def patch(self, request):
        user = request.user
        payload = request.data or {}
        updated = False

        map_fields = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'phone_number': 'phone_number',
        }
        for src, attr in map_fields.items():
            if src in payload and hasattr(user, attr):
                setattr(user, attr, payload[src])
                updated = True

        if updated:
            user.save()

        # Return updated snapshot
        return self.get(request)


class UploadAvatarView(APIView):
    """
    Endpoint to upload user profile avatar/photo.
    POST /api/v1/auth/profile/upload-avatar/
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user
        avatar_file = request.FILES.get('avatar') or request.FILES.get('photo')

        if not avatar_file:
            return Response(
                {'error': 'No avatar file provided. Use "avatar" or "photo" field.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return Response(
                {'error': f'Invalid file type. Allowed: {", ".join(allowed_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if avatar_file.size > max_size:
            return Response(
                {'error': 'File too large. Maximum size is 5MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get or create practitioner for user
            from apps.competitions.models import Practitioner

            practitioner = Practitioner.objects.filter(user=user).first()
            if not practitioner:
                # Create practitioner if doesn't exist
                practitioner = Practitioner.objects.create(
                    user=user,
                    first_name=user.first_name or '',
                    last_name=user.last_name or '',
                    email=user.email or '',
                )

            # Delete old photo if exists
            if practitioner.photo:
                try:
                    practitioner.photo.delete(save=False)
                except Exception:
                    pass

            # Save new photo
            practitioner.photo = avatar_file
            practitioner.save()

            # Build absolute URL
            photo_url = None
            if practitioner.photo:
                photo_url = request.build_absolute_uri(practitioner.photo.url)
                # Ensure HTTPS in production
                if 'martialcomp.com' in photo_url and photo_url.startswith('http://'):
                    photo_url = photo_url.replace('http://', 'https://')

            return Response({
                'success': True,
                'message': 'Avatar uploaded successfully',
                'avatar_url': photo_url,
                'photo_url': photo_url,  # Alias for compatibility
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error uploading avatar: {e}")
            return Response(
                {'error': f'Failed to upload avatar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SocialLoginBase(APIView):
    permission_classes = [permissions.AllowAny]

    provider = None  # 'google' or 'facebook'

    def post(self, request):
        token = request.data.get('token')  # id_token (Google) or access_token (Facebook)
        if not token:
            return Response({'error': 'token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = self.validate_and_get_user(token)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Issue tokens (same as LoginView)
        jwt_refresh = JWTRefreshToken.for_user(user)
        jti = str(uuid.uuid4())
        jwt_refresh.access_token['jti'] = jti

        AccessTokenLog.objects.create(
            user=user,
            jti=jti,
            expires_at=timezone.now() + datetime.timedelta(minutes=60),
            device_id=None,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=self.get_client_ip(request),
            tenant=getattr(request, 'tenant', None)
        )

        response_data = {
            'access': str(jwt_refresh.access_token),
            'refresh': str(jwt_refresh),
            'user': UserSerializer(user).data,
            'expires_in': 3600,
        }
        return Response(TokenSerializer(response_data).data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def validate_and_get_user(self, token):
        raise NotImplementedError


class SocialLoginGoogleView(SocialLoginBase):
    provider = 'google'

    def validate_and_get_user(self, id_token:str):
        # Minimal validation placeholder: in production, verify with Google tokeninfo or google-auth library
        # Accept basic JWT decoding to extract email; here we fallback to a simple stub for Phase 1
        import base64, json
        email = None
        try:
            parts = id_token.split('.')
            if len(parts) >= 2:
                payload_b64 = parts[1] + '==='  # pad
                payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
                email = payload.get('email')
        except Exception:
            pass
        if not email:
            # Fallback: allow direct email token in dev
            email = id_token if '@' in id_token else None
        if not email:
            raise Exception('Invalid Google token')

        # Find or create user
        user, _ = User.objects.get_or_create(username=email, defaults={'email': email, 'is_active': True})
        return user


class SocialLoginFacebookView(SocialLoginBase):
    provider = 'facebook'

    def validate_and_get_user(self, access_token:str):
        # Minimal validation placeholder: in production, call https://graph.facebook.com/me?fields=id,name,email&access_token=...
        # For Phase 1, accept an email passed as token for dev/testing
        email = access_token if '@' in access_token else None
        if not email:
            raise Exception('Invalid Facebook token')
        user, _ = User.objects.get_or_create(username=email, defaults={'email': email, 'is_active': True})
        return user



class DeviceRegistrationView(APIView):
    """
    Vue pour enregistrer un nouvel appareil
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = DeviceRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            device = serializer.save()
            return Response(DeviceRegistrationSerializer(device).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """Récupérer tous les appareils enregistrés pour l'utilisateur"""
        devices = DeviceRegistration.objects.filter(user=request.user)
        serializer = DeviceRegistrationSerializer(devices, many=True)
        return Response(serializer.data)


class PKCEInitView(APIView):
    """
    Vue pour initialiser le flux PKCE (sans authentification)
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PKCEInitSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            pkce_session = serializer.save()
            
            return Response({
                'auth_code': pkce_session.auth_code,
                'expires_in': int((pkce_session.expires_at - timezone.now()).total_seconds())
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PKCEAuthorizationView(APIView):
    """
    Vue pour autoriser un flux PKCE (avec authentification)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        auth_code = request.data.get('auth_code')
        if not auth_code:
            return Response(
                {'error': _("Code d'autorisation requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pkce_session = PKCESession.objects.get(auth_code=auth_code, used=False)
        except PKCESession.DoesNotExist:
            return Response(
                {'error': _("Code d'autorisation invalide.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if pkce_session.is_expired:
            return Response(
                {'error': _("Code d'autorisation expiré.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Associer l'utilisateur à la session PKCE
        pkce_session.user = request.user
        pkce_session.save(update_fields=['user'])
        
        return Response({
            'success': True,
            'message': _("Autorisation accordée avec succès.")
        })


class PKCECompleteView(APIView):
    """
    Vue pour compléter le flux PKCE et échanger un code contre des tokens JWT
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PKCECompleteSerializer(data=request.data)
        if serializer.is_valid():
            # Récupérer les objets validés
            pkce_session = serializer.validated_data['pkce_session']
            user = serializer.validated_data['user']
            
            if not user:
                return Response(
                    {'error': _("Session PKCE non autorisée.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Générer les tokens JWT
            jwt_refresh = JWTRefreshToken.for_user(user)
            
            # Multi-tenant context
            tenant = getattr(request, 'tenant', None) or pkce_session.tenant
            if tenant:
                jwt_refresh['tenant_id'] = str(tenant.id)
                jwt_refresh['tenant_name'] = tenant.name
            
            # Définis le JTI pour le token d'accès pour les logs
            jti = str(uuid.uuid4())
            jwt_refresh.access_token['jti'] = jti
            
            # Créer un RefreshToken dans la base de données
            expires_in_days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
            expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
            
            db_refresh_token = RefreshToken.objects.create(
                user=user,
                token=str(jwt_refresh),
                expires_at=expires_at,
                device_id=None,  # À remplir avec un appareil si disponible
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant,
                code_challenge=pkce_session.code_challenge,
                code_challenge_method=pkce_session.code_challenge_method,
            )
            
            # Enregistrer le jeton d'accès dans les logs
            access_token_expires = timezone.now() + datetime.timedelta(minutes=60)  # 1 heure par défaut
            
            AccessTokenLog.objects.create(
                user=user,
                jti=jti,
                expires_at=access_token_expires,
                device_id=None,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Préparer la réponse
            response_data = {
                'access': str(jwt_refresh.access_token),
                'refresh': str(jwt_refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 heure pour le token d'accès
            }
            
            return Response(TokenSerializer(response_data).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RevokeTokenView(APIView):
    """
    Vue pour révoquer un token spécifique ou tous les tokens d'un utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        device_id = request.data.get('device_id')
        all_devices = request.data.get('all_devices', False)
        
        if device_id:
            # Révoquer tous les tokens pour un appareil spécifique
            RefreshToken.objects.filter(
                user=request.user, 
                device_id=device_id, 
                revoked=False
            ).update(revoked=True)
            
            return Response({'message': _("Tokens révoqués pour l'appareil spécifié.")})
        
        elif all_devices:
            # Révoquer tous les tokens pour tous les appareils
            RefreshToken.objects.filter(
                user=request.user,
                revoked=False
            ).update(revoked=True)
            
            return Response({'message': _("Tous les tokens ont été révoqués.")})
        
        return Response(
            {'error': _("Veuillez spécifier device_id ou all_devices=True.")},
            status=status.HTTP_400_BAD_REQUEST
        )


class SSOGenerateTokenView(APIView):
    """
    Génère un token SSO à usage unique pour permettre la connexion automatique
    depuis l'application mobile vers le site web.

    Le token expire après 60 secondes et ne peut être utilisé qu'une seule fois.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        user = request.user
        redirect_url = request.data.get('redirect_url', '/fr/competitions/dashboard/club/')

        # Générer un token sécurisé
        token = secrets.token_urlsafe(48)

        # Le token expire après 60 secondes (suffisant pour la redirection)
        expires_at = timezone.now() + datetime.timedelta(seconds=60)

        # Multi-tenant context
        tenant = getattr(request, 'tenant', None)

        # Créer le token SSO
        sso_token = SSOToken.objects.create(
            user=user,
            token=token,
            redirect_url=redirect_url,
            expires_at=expires_at,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            tenant=tenant
        )

        # Nettoyer les anciens tokens expirés de cet utilisateur
        SSOToken.objects.filter(
            user=user,
            expires_at__lt=timezone.now()
        ).delete()

        return Response({
            'token': token,
            'expires_in': 60,
            'sso_url': f'/sso/login/?token={token}',
        })

    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PasswordChangeView(APIView):
    """
    Vue pour changer le mot de passe d'un utilisateur authentifié
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()

            # Révoquer tous les tokens existants pour forcer une reconnexion
            RefreshToken.objects.filter(user=request.user, revoked=False).update(revoked=True)

            return Response({
                'success': True,
                'message': _("Votre mot de passe a été modifié avec succès. Veuillez vous reconnecter.")
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    Vue pour demander une réinitialisation de mot de passe (mot de passe oublié)
    Envoie un email avec un lien de réinitialisation
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email__iexact=email)

                # Générer le token et l'uid
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Construire l'URL de réinitialisation
                frontend_url = getattr(settings, 'FRONTEND_URL', 'https://martialcomp.com')
                reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"

                # Envoyer l'email
                subject = _("Réinitialisation de votre mot de passe MartialComp")
                message = _(
                    f"Bonjour {user.first_name or user.username},\n\n"
                    f"Vous avez demandé la réinitialisation de votre mot de passe.\n"
                    f"Cliquez sur le lien suivant pour définir un nouveau mot de passe :\n\n"
                    f"{reset_url}\n\n"
                    f"Ce lien est valable pendant 24 heures.\n\n"
                    f"Si vous n'avez pas fait cette demande, ignorez cet email.\n\n"
                    f"L'équipe MartialComp"
                )

                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    # Log l'erreur mais ne pas révéler à l'utilisateur
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erreur envoi email reset password: {e}")

            except User.DoesNotExist:
                # Ne pas révéler si l'email existe ou non (sécurité)
                pass

            # Toujours retourner succès pour ne pas révéler si l'email existe
            return Response({
                'success': True,
                'message': _("Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.")
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Vue pour confirmer la réinitialisation du mot de passe avec le token
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            uid = serializer.validated_data['uid']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']

            try:
                # Décoder l'uid pour obtenir l'utilisateur
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({
                    'success': False,
                    'message': _("Lien de réinitialisation invalide.")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Vérifier le token
            if not default_token_generator.check_token(user, token):
                return Response({
                    'success': False,
                    'message': _("Lien de réinitialisation expiré ou déjà utilisé.")
                }, status=status.HTTP_400_BAD_REQUEST)

            # Mettre à jour le mot de passe
            user.set_password(new_password)
            user.save()

            # Révoquer tous les tokens existants
            RefreshToken.objects.filter(user=user, revoked=False).update(revoked=True)

            return Response({
                'success': True,
                'message': _("Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.")
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)