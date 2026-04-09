#!/usr/bin/env python3
"""Patch event_detail.html to add category assignment modal."""

filepath = "/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/events/event_detail.html"

with open(filepath, "r") as f:
    content = f.read()

# 1. Make practitioner names clickable
old = "{{ participant.practitioner.first_name }} {{ participant.practitioner.last_name }}"
new = '''{% if participant.comp_registration %}<span style="cursor:pointer;color:#60a5fa;text-decoration:underline" onclick="openCatModal({{ participant.comp_registration.id }}, this)" data-cats="{{ participant.assigned_categories }}"><i class="fas fa-edit" style="font-size:0.7em"></i> {{ participant.practitioner.first_name }} {{ participant.practitioner.last_name }} <span class="badge bg-info cat-count" style="font-size:0.65em">{{ participant.assigned_categories|length }} cat.</span></span>{% else %}{{ participant.practitioner.first_name }} {{ participant.practitioner.last_name }}{% endif %}'''
content = content.replace(old, new, 1)

# 2. Add modal + JS before the last endblock
modal_js = '''
<!-- Category Assignment Modal -->
<div class="modal fade" id="catModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content" style="background:#1e293b;color:#fff">
      <div class="modal-header border-secondary">
        <h5 class="modal-title" id="catModalTitle">Assign categories</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        {% for ct_data in comp_types_with_cats %}
        <div class="mb-3">
          <h6 style="color:#f59e0b"><i class="fas fa-trophy me-1"></i>{{ ct_data.type.name }}</h6>
          {% for cat in ct_data.categories %}
          <div class="form-check">
            <input class="form-check-input cat-cb" type="checkbox" value="{{ cat.id }}" id="mcat_{{ cat.id }}">
            <label class="form-check-label" for="mcat_{{ cat.id }}">{{ cat.name }}{% if cat.gender and cat.gender != 'mixed' %} <small class="text-muted">({{ cat.get_gender_display }})</small>{% endif %}</label>
          </div>
          {% endfor %}
        </div>
        {% empty %}
        <p class="text-muted">No categories available</p>
        {% endfor %}
      </div>
      <div class="modal-footer border-secondary">
        <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
        <button class="btn btn-primary btn-sm" onclick="saveCats()"><i class="fas fa-save me-1"></i>Save</button>
      </div>
    </div>
  </div>
</div>
<script>
let _regId=null,_el=null;
function openCatModal(regId,el){
  _regId=regId;_el=el;
  document.querySelectorAll('.cat-cb').forEach(function(c){c.checked=false;});
  try{
    var raw=el.getAttribute('data-cats')||'[]';
    raw=raw.replace(/'/g,'"');
    var cats=JSON.parse(raw);
    cats.forEach(function(id){var c=document.getElementById('mcat_'+id);if(c)c.checked=true;});
  }catch(e){console.log('parse error',e);}
  new bootstrap.Modal(document.getElementById('catModal')).show();
}
function saveCats(){
  if(!_regId)return;
  var ids=[];
  document.querySelectorAll('.cat-cb:checked').forEach(function(c){ids.push(parseInt(c.value));});
  var csrftoken='';
  var cookies=document.cookie.split(';');
  for(var i=0;i<cookies.length;i++){
    var c=cookies[i].trim();
    if(c.indexOf('csrftoken=')==0){csrftoken=c.substring(10);break;}
  }
  fetch('/'+document.documentElement.lang+'/competitions/events/registration/update-categories/',{
    method:'POST',
    headers:{'Content-Type':'application/json','X-CSRFToken':csrftoken},
    body:JSON.stringify({registration_id:_regId,category_ids:ids})
  }).then(function(r){return r.json();}).then(function(d){
    if(d.success){
      bootstrap.Modal.getInstance(document.getElementById('catModal')).hide();
      if(_el){
        var badge=_el.querySelector('.cat-count');
        if(badge)badge.textContent=ids.length+' cat.';
        _el.setAttribute('data-cats',JSON.stringify(ids));
      }
      location.reload();
    }else{alert(d.error||'Error');}
  }).catch(function(e){alert('Network error: '+e);});
}
</script>
'''

last_endblock = content.rfind("{% endblock %}")
if last_endblock != -1:
    content = content[:last_endblock] + modal_js + "\n" + content[last_endblock:]
    with open(filepath, "w") as f:
        f.write(content)
    print("Template patched OK")
else:
    print("ERROR: endblock not found")
