#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour mettre à jour directement le template du profil coach
"""
import os

# Chemin du template
template_file = "competitions/templates/onboarding/coach/profile.html"

if not os.path.exists(template_file):
    print(f"Le fichier {template_file} n'existe pas.")
    exit(1)

# Lire le contenu du template
with open(template_file, "r", encoding="utf-8") as f:
    content = f.read()

# Sauvegarder l'original
with open(f"{template_file}.original", "w", encoding="utf-8") as f:
    f.write(content)
    
print(f"Sauvegarde du template original créée: {template_file}.original")

# Contenu mis à jour - version complète
new_content = """{% extends "onboarding/base.html" %}
{% load static i18n %}

{% block title %}{% trans "Complete Your Coach Profile" %}{% endblock %}

{% block content %}
<div class="container-fluid py-5">
    <div class="row justify-content-center">
        <div class="col-md-10">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0">{% trans "Coach Profile Setup" %}</h4>
                </div>
                <div class="card-body">
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        
                        <!-- Basic Information -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="border-bottom pb-2">{% trans "Basic Information" %}</h5>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group">
                                    <label>{% trans "Name" %}</label>
                                    <input type="text" class="form-control" value="{{ user.first_name }} {{ user.last_name }}" readonly>
                                </div>
                            </div>
                            <div class="col-md-6">
                                {{ profile_form.photo|as_crispy_field }}
                            </div>
                            <div class="col-12">
                                {{ profile_form.bio|as_crispy_field }}
                            </div>
                            <div class="col-12">
                                {{ profile_form.teaching_philosophy|as_crispy_field }}
                            </div>
                        </div>

                        <!-- Experience and Certification -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="border-bottom pb-2">{% trans "Experience & Certification" %}</h5>
                            </div>
                            <div class="col-md-6">
                                {{ profile_form.profile_type|as_crispy_field }}
                            </div>
                            <div class="col-md-6">
                                {{ profile_form.years_of_experience|as_crispy_field }}
                            </div>
                            <div class="col-md-6">
                                {{ profile_form.primary_teaching_place|as_crispy_field }}
                            </div>
                            <div class="col-md-6">
                                {{ profile_form.certification_info|as_crispy_field }}
                            </div>
                        </div>

                        <!-- Discipline Expertise -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="border-bottom pb-2">{% trans "Discipline Expertise" %}</h5>
                                <p class="text-muted">{% trans "Add your expertise in different disciplines" %}</p>
                            </div>
                            <div class="col-12">
                                <div id="expertise-formset">
                                    {{ expertise_formset.management_form }}
                                    {% for form in expertise_formset %}
                                        <div class="expertise-form row mb-3">
                                            <div class="col-md-4">
                                                {{ form.discipline|as_crispy_field }}
                                            </div>
                                            <div class="col-md-3">
                                                {{ form.years_of_experience|as_crispy_field }}
                                            </div>
                                            <div class="col-md-3">
                                                {{ form.level|as_crispy_field }}
                                            </div>
                                            <div class="col-md-2">
                                                {% if form.instance.pk %}
                                                    {{ form.DELETE|as_crispy_field }}
                                                {% endif %}
                                            </div>
                                            <div class="col-12">
                                                {{ form.specialization|as_crispy_field }}
                                            </div>
                                            {% for hidden in form.hidden_fields %}
                                                {{ hidden }}
                                            {% endfor %}
                                        </div>
                                    {% endfor %}
                                </div>
                                <button type="button" class="btn btn-sm btn-secondary" id="add-expertise">
                                    <i class="fas fa-plus"></i> {% trans "Add Another Discipline" %}
                                </button>
                            </div>
                        </div>

                        <!-- Privacy Settings -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="border-bottom pb-2">{% trans "Privacy Settings" %}</h5>
                            </div>
                            <div class="col-12">
                                <div class="form-check">
                                    <input type="checkbox" class="form-check-input" name="show_email" id="show_email" 
                                           {% if profile_form.instance.visibility_settings.show_email %}checked{% endif %}>
                                    <label class="form-check-label" for="show_email">
                                        {% trans "Show email address on public profile" %}
                                    </label>
                                </div>
                                <div class="form-check">
                                    <input type="checkbox" class="form-check-input" name="show_phone" id="show_phone"
                                           {% if profile_form.instance.visibility_settings.show_phone %}checked{% endif %}>
                                    <label class="form-check-label" for="show_phone">
                                        {% trans "Show phone number on public profile" %}
                                    </label>
                                </div>
                                <div class="form-check">
                                    <input type="checkbox" class="form-check-input" name="show_location" id="show_location"
                                           {% if profile_form.instance.visibility_settings.show_location %}checked{% endif %}>
                                    <label class="form-check-label" for="show_location">
                                        {% trans "Show location on public profile" %}
                                    </label>
                                </div>
                                <div class="form-check">
                                    <input type="checkbox" class="form-check-input" name="show_achievements" id="show_achievements"
                                           {% if profile_form.instance.visibility_settings.show_achievements %}checked{% endif %}>
                                    <label class="form-check-label" for="show_achievements">
                                        {% trans "Show achievements on public profile" %}
                                    </label>
                                </div>
                                <div class="form-check">
                                    <input type="checkbox" class="form-check-input" name="allow_contact" id="allow_contact"
                                           {% if profile_form.instance.visibility_settings.allow_contact %}checked{% endif %}>
                                    <label class="form-check-label" for="allow_contact">
                                        {% trans "Allow students to contact me directly" %}
                                    </label>
                                </div>
                                <div class="form-check">
                                    <input type="checkbox" class="form-check-input" name="show_schedule" id="show_schedule"
                                           {% if profile_form.instance.visibility_settings.show_schedule %}checked{% endif %}>
                                    <label class="form-check-label" for="show_schedule">
                                        {% trans "Show teaching schedule publicly" %}
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-12">
                                <button type="submit" class="btn btn-primary">
                                    {% trans "Save Profile" %}
                                </button>
                                <a href="{% url 'onboarding:final' %}" class="btn btn-secondary">
                                    {% trans "Skip for now" %}
                                </a>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Gestion du formset d'expertise
    const addButton = document.getElementById('add-expertise');
    const formsetDiv = document.getElementById('expertise-formset');
    const totalFormsInput = document.querySelector('[name$=TOTAL_FORMS]');
    
    addButton.addEventListener('click', function() {
        const formCount = parseInt(totalFormsInput.value);
        const newForm = document.querySelector('.expertise-form').cloneNode(true);
        
        // Mettre à jour les IDs et names
        newForm.innerHTML = newForm.innerHTML.replace(/form-\d+/g, `form-${formCount}`);
        
        // Vider les valeurs
        newForm.querySelectorAll('input[type=text], textarea, select').forEach(field => {
            field.value = '';
        });
        
        // Ajouter le formulaire
        formsetDiv.insertBefore(newForm, addButton);
        totalFormsInput.value = formCount + 1;
    });
});
</script>
{% endblock %}"""

# Écrire le nouveau contenu
with open(template_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"✓ Template mis à jour avec succès: {template_file}")
print("Le nouveau template inclut:")
print("1. Le champ profile_type correctement placé")
print("2. Le champ primary_teaching_place modifié pour Club d'enseignement principal")
print("3. Une meilleure organisation des champs de formulaire")
print("\nRedémarrez le serveur Django pour voir les changements.")