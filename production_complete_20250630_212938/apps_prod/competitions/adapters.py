from django.conf import settings
from django.shortcuts import redirect
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MartialCompAccountAdapter(DefaultAccountAdapter):
  """Adapter personnalisé pour l'inscription standard."""

  def save_user(self, request, user, form, commit=True):
	  user = super().save_user(request, user, form, commit=False)

	  if commit:
		  user.save()
		  # Créer un profil utilisateur
		  try:
			  from competitions.models.users import UserProfile
			  UserProfile.objects.get_or_create(
				  user=user,
				  defaults={
					  'role': 'spectator',
					  'onboarding_step': 'role_selection',
					  'onboarding_completed': False
				  }
			  )
		  except ImportError:
			  pass

	  return user

  def get_signup_redirect_url(self, request):
	  return getattr(settings, 'SIGNUP_REDIRECT_URL', '/onboarding/role/')

class MartialCompSocialAccountAdapter(DefaultSocialAccountAdapter):
  """Adapter personnalisé pour l'inscription via réseaux sociaux."""

  def populate_user(self, request, sociallogin, data):
	  user = super().populate_user(request, sociallogin, data)

	  provider = sociallogin.account.provider
	  if provider == 'google':
		  user.first_name = data.get('given_name', '')
		  user.last_name = data.get('family_name', '')
	  elif provider == 'facebook':
		  user.first_name = data.get('first_name', '')
		  user.last_name = data.get('last_name', '')

	  return user

  def save_user(self, request, sociallogin, form=None):
	  user = super().save_user(request, sociallogin, form)

	  # Créer un profil utilisateur
	  try:
		  from competitions.models.users import UserProfile
		  UserProfile.objects.get_or_create(
			  user=user,
			  defaults={
				  'role': 'spectator',
				  'onboarding_step': 'role_selection',
				  'onboarding_completed': False
			  }
		  )
	  except ImportError:
		  pass

	  return user
