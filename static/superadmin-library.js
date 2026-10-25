/* CA FirmHub SuperAdmin — Firm Library (Designed & Built by Harsh Pala) */
(function(){
if(window.__cafhSaLibrary)return;window.__cafhSaLibrary=true;
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function injectTab(){
  var tabEls=document.querySelectorAll('.tab');if(!tabEls.length)return;
  var bar=tabEls[0].parentElement;if(document.getElementById('tab-btn-library'))return;
  var btn=document.createElement('div');btn.className='tab';btn.id='tab-btn-library';btn.textContent='Firm Library';
  btn.onclick=function(){switchToLibrary();};bar.appendChild(btn);
  var app=document.getElementById('app');if(!app||document.getElementById('tab-library'))return;
  var panel=document.createElement('div');panel.id='tab-library';panel.style.display='none';
  panel.innerHTML='<div class="card" style="margin:16px"><div class="card-h" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px"><div><strong>Firm-specific Study Material</strong><div style="font-size:12px;color:var(--text3);font-weight:400">Visible only to the selected firm staff</div></div><button class="btn btn-p" onclick="saLibOpenAdd()">+ Add material</button></div><div class="card-b"><div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center"><label style="font-size:12px;font-weight:600">Filter firm</label><select id="sa-lib-firm-filter" onchange="saLibLoad()" style="padding:6px 10px;border:1.5px solid var(--border);border-radius:var(--r);font:inherit"><option value="">All firms</option></select></div><div style="overflow:auto"><table class="dt"><thead><tr><th>Firm</th><th>Title</th><th>Category</th><th>URL</th><th>Active</th><th></th></tr></thead><tbody id="sa-lib-tbody"><tr><td colspan="6" class="empty">Loading…</td></tr></tbody></table></div></div></div>';
  var last=document.getElementById('tab-templates')||document.getElementById('tab-users')||document.getElementById('tab-firms');
  if(last&&last.parentElement)last.parentElement.appendChild(panel);else app.appendChild(panel);
  if(!document.getElementById('sa-lib-mo')){
    var mo=document.createElement('div');mo.className='mo';mo.id='sa-lib-mo';
    mo.innerHTML='<div class="md" style="max-width:520px"><div class="md-h"><h3 id="sa-lib-mo-title">Add firm material</h3><button class="md-x" onclick="closeMo(\'sa-lib-mo\')">×</button></div><div class="md-b"><input type="hidden" id="sa-lib-id"><div class="fg"><label>Firm *</label><select id="sa-lib-firm"></select></div><div class="fg"><label>Title *</label><input id="sa-lib-title"></div><div class="fg"><label>URL *</label><input id="sa-lib-url" placeholder="https://..."></div><div class="fg"><label>Category</label><input id="sa-lib-cat" value="Firm material"></div><div class="fg"><label>Source</label><input id="sa-lib-source"></div><div class="fg"><label>Description</label><textarea id="sa-lib-desc" rows="2"></textarea></div><div class="fg"><label><input type="checkbox" id="sa-lib-active" checked> Active</label></div></div><div class="md-f"><button class="btn btn-o" onclick="closeMo(\'sa-lib-mo\')">Cancel</button><button class="btn btn-p" onclick="saLibSave()">Save</button></div></div>';
    document.body.appendChild(mo);
  }
  if(!window.__saLibSwitchPatched&&typeof window.switchTab==='function'){
    window.__saLibSwitchPatched=true;var _st=window.switchTab;
    window.switchTab=function(t){if(t==='library')return switchToLibrary();
      var p=document.getElementById('tab-library');if(p)p.style.display='none';
      var b=document.getElementById('tab-btn-library');if(b)b.classList.remove('on');return _st(t);};
  }
}
window.switchToLibrary=function(){
  document.querySelectorAll('.tab').forEach(function(el){el.classList.remove('on');});
  var libBtn=document.getElementById('tab-btn-library');if(libBtn)libBtn.classList.add('on');
  ['tab-firms','tab-users','tab-templates'].forEach(function(id){var el=document.getElementById(id);if(el)el.style.display='none';});
  var panel=document.getElementById('tab-library');if(panel)panel.style.display='';
  saLibPopulateFirms();saLibLoad();
};
function saLibPopulateFirms(){
  var firms=(typeof ALL_FIRMS!=='undefined'&&ALL_FIRMS)?ALL_FIRMS:[];
  var filter=document.getElementById('sa-lib-firm-filter'),sel=document.getElementById('sa-lib-firm');
  var opts=firms.map(function(f){return '<option value="'+f.id+'">'+esc(f.name)+'</option>';}).join('');
  if(filter){var cur=filter.value;filter.innerHTML='<option value="">All firms</option>'+opts;filter.value=cur;}
  if(sel)sel.innerHTML='<option value="">Select firm…</option>'+opts;
}
window.saLibLoad=async function(){
  var tb=document.getElementById('sa-lib-tbody');if(!tb)return;
  tb.innerHTML='<tr><td colspan="6" class="empty">Loading…</td></tr>';
  try{
    if(typeof ALL_FIRMS==='undefined'||!ALL_FIRMS||!ALL_FIRMS.length){if(typeof loadFirms==='function')await loadFirms();}
    saLibPopulateFirms();
    var fid=(document.getElementById('sa-lib-firm-filter')||{}).value||'';
    var rows=await saFetch('/api/superadmin/library'+(fid?('?firm_id='+encodeURIComponent(fid)):''));
    window.__saLibRows=rows;
    if(!rows.length){tb.innerHTML='<tr><td colspan="6" class="empty">No firm materials yet.</td></tr>';return;}
    var nameById={};(ALL_FIRMS||[]).forEach(function(f){nameById[f.id]=f.name;});
    tb.innerHTML=rows.map(function(r,idx){
      var fname=r.firm_name||nameById[r.firm_id]||('#'+r.firm_id);
      return '<tr><td>'+esc(fname)+'</td><td><strong>'+esc(r.title)+'</strong></td><td>'+esc(r.category||'')+
        '</td><td style="max-width:180px;overflow:hidden;text-overflow:ellipsis"><a href="'+esc(r.url)+'" target="_blank">'+esc(r.url)+
        '</a></td><td>'+(r.is_active?'Yes':'No')+'</td><td><button class="btn btn-xs btn-o" onclick="saLibEditIdx('+idx+
        ')">Edit</button> <button class="btn btn-xs btn-err" onclick="saLibDelete('+r.id+')">Delete</button></td></tr>';
    }).join('');
  }catch(e){tb.innerHTML='<tr><td colspan="6" class="empty">'+esc(e.message)+'</td></tr>';}
};
window.saLibOpenAdd=function(){
  saLibPopulateFirms();
  document.getElementById('sa-lib-mo-title').textContent='Add firm material';
  document.getElementById('sa-lib-id').value='';
  document.getElementById('sa-lib-title').value='';
  document.getElementById('sa-lib-url').value='';
  document.getElementById('sa-lib-cat').value='Firm material';
  document.getElementById('sa-lib-source').value='';
  document.getElementById('sa-lib-desc').value='';
  document.getElementById('sa-lib-active').checked=true;
  var filter=document.getElementById('sa-lib-firm-filter');
  if(filter&&filter.value)document.getElementById('sa-lib-firm').value=filter.value;
  openMo('sa-lib-mo');
};
window.saLibEditIdx=function(idx){var r=(window.__saLibRows||[])[idx];if(!r)return;saLibPopulateFirms();
  document.getElementById('sa-lib-mo-title').textContent='Edit firm material';
  document.getElementById('sa-lib-id').value=r.id||'';
  document.getElementById('sa-lib-firm').value=r.firm_id||'';
  document.getElementById('sa-lib-title').value=r.title||'';
  document.getElementById('sa-lib-url').value=r.url||'';
  document.getElementById('sa-lib-cat').value=r.category||'Firm material';
  document.getElementById('sa-lib-source').value=r.source||'';
  document.getElementById('sa-lib-desc').value=r.description||'';
  document.getElementById('sa-lib-active').checked=r.is_active!==false;openMo('sa-lib-mo');
};
window.saLibSave=async function(){
  var id=document.getElementById('sa-lib-id').value;
  var body={firm_id:parseInt(document.getElementById('sa-lib-firm').value,10),
    title:document.getElementById('sa-lib-title').value.trim(),
    url:document.getElementById('sa-lib-url').value.trim(),
    category:document.getElementById('sa-lib-cat').value.trim()||'Firm material',
    source:document.getElementById('sa-lib-source').value.trim(),
    description:document.getElementById('sa-lib-desc').value.trim(),
    is_active:document.getElementById('sa-lib-active').checked};
  if(!body.firm_id||!body.title||!body.url){toast('Firm, title and URL required','err');return;}
  try{
    if(id)await saFetch('/api/superadmin/library/'+id,{method:'PUT',body:JSON.stringify(body)});
    else await saFetch('/api/superadmin/library',{method:'POST',body:JSON.stringify(body)});
    toast('Saved','ok');closeMo('sa-lib-mo');saLibLoad();
  }catch(e){toast(e.message||'Save failed','err');}
};
window.saLibDelete=async function(id){
  if(!confirm('Delete this firm material?'))return;
  try{await saFetch('/api/superadmin/library/'+id,{method:'DELETE'});toast('Deleted','ok');saLibLoad();}
  catch(e){toast(e.message||'Delete failed','err');}
};
var obs=new MutationObserver(function(){if(document.getElementById('app')&&document.getElementById('app').style.display!=='none')injectTab();});
obs.observe(document.documentElement,{childList:true,subtree:true,attributes:true});
if(document.readyState!=='loading')injectTab();else document.addEventListener('DOMContentLoaded',injectTab);
})();
