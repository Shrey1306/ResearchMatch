// ─── Global state ──────────────────────────────────────────────────────────
let allResearchers = [];
let uniqueResearchAreas = new Set();
let selectedResearchAreas = new Set();
let currentModel = 'scraping';           // default LLM source

// ─── Helpers ───────────────────────────────────────────────────────────────
function cleanResearchArea(area) {
    const abbreviations = {
        ai:'Artificial Intelligence', ml:'Machine Learning', nlp:'Natural Language Processing',
        hci:'Human Computer Interaction', iot:'Internet of Things', ar:'Augmented Reality',
        vr:'Virtual Reality', xr:'Extended Reality', os:'Operating Systems', db:'Database',
        ui:'User Interface', ux:'User Experience'
    };
    const lowercase = new Set(['a','an','the','and','or','but','nor','for','yet','so','at',
                               'by','in','of','on','to','up','as']);
    return area.toLowerCase().trim()
        .replace(/[&\/\\#,+()$~%.'":*?<>{}]/g,' ')
        .replace(/\s+/g,' ')
        .split(' ')
        .map(w=>{
            if(abbreviations[w]) return abbreviations[w];
            return lowercase.has(w) ? w : w.charAt(0).toUpperCase()+w.slice(1);
        })
        .join(' ')
        .replace(/^(and|or|&)\s+/i,'')
        .replace(/\s+(and|or|&)$/i,'')
        .trim();
}

// Build uniqueResearchAreas for currentModel
function rebuildTopics() {
    uniqueResearchAreas.clear();
    const seen=new Set();
    allResearchers.forEach(r=>{
        (r.research_areas?.[currentModel]||[]).forEach(a=>{
            const c=cleanResearchArea(a);
            if(c && !seen.has(c)){ seen.add(c); uniqueResearchAreas.add(c); }
        });
    });
    populateResearchAreasDropdown();
}

// ─── DOM ready ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', ()=>{
    document.getElementById('last-updated').textContent = new Date().toLocaleString();

    // fetch JSON
    fetch('../results.json')
        .then(r=>{
            if(!r.ok) throw new Error(r.status);
            return r.json();
        })
        .then(data=>{
            allResearchers=data;
            rebuildTopics();
        })
        .catch(e=>{
            console.error('Loading error',e);
            document.getElementById('resultsContainer').innerHTML=
               '<p>Error loading data.</p>';
        });

    // radio change
    document.querySelectorAll('input[name="model"]').forEach(radio=>{
        radio.addEventListener('change',e=>{
            currentModel=e.target.value;
            selectedResearchAreas.clear();
            updateSelectedTags();
            rebuildTopics();
        });
    });

    // find matches
    document.getElementById('findMatches').addEventListener('click',()=>{
        const selected=Array.from(selectedResearchAreas);
        const useCitations=document.getElementById('tfidfToggle').checked;

        let matches=allResearchers.filter(r=>{
            const list=r.research_areas?.[currentModel]||[];
            return list.some(a=>selected.includes(cleanResearchArea(a)));
        });

        if(useCitations){
            matches.sort((a,b)=>(b.statistics?.all?.citations||0)-(a.statistics?.all?.citations||0));
        }
        displayResearchers(matches);
    });
});

// ─── UI builders ───────────────────────────────────────────────────────────
function populateResearchAreasDropdown(){
    const box=document.getElementById('topicsContainer');
    box.innerHTML='';
    const sel=document.createElement('select');
    sel.id='researchAreasSelect'; sel.multiple=true; sel.size=15;

    const tip=document.createElement('option');
    tip.disabled=true; tip.textContent='↑↓ navigate, space select, or click';
    sel.appendChild(tip);

    Array.from(uniqueResearchAreas).sort().forEach(area=>{
        const op=document.createElement('option');
        op.value=area; op.textContent=area;
        sel.appendChild(op);
    });

    sel.addEventListener('keydown',e=>{
        if(e.code==='Space'){e.preventDefault();toggleOptionSelection(sel.options[sel.selectedIndex]);}
    });
    sel.addEventListener('mousedown',e=>{
        e.preventDefault();
        const op=e.target.closest('option');if(op&&!op.disabled)toggleOptionSelection(op);
    });

    box.appendChild(sel);
    updateSelectedTags();
}

function toggleOptionSelection(op){
    op.selected=!op.selected;
    selectedResearchAreas.clear();
    Array.from(document.getElementById('researchAreasSelect').selectedOptions)
        .filter(o=>!o.disabled).forEach(o=>selectedResearchAreas.add(o.value));
    updateSelectedTags();
}

function updateSelectedTags(){
    const wrap=document.getElementById('selectedTags');
    wrap.innerHTML='';
    if(!selectedResearchAreas.size){
        wrap.innerHTML='<span class="no-tags-message">No research areas selected</span>';
        return;
    }
    selectedResearchAreas.forEach(area=>{
        const tag=document.createElement('span'); tag.className='tag';
        tag.innerHTML=`${area}<span class="remove" data-area="${area}">✕</span>`;
        tag.querySelector('.remove').addEventListener('click',e=>{
            selectedResearchAreas.delete(area);
            const op=document.querySelector(`#researchAreasSelect option[value="${area}"]`);
            if(op) op.selected=false;
            updateSelectedTags();
        });
        wrap.appendChild(tag);
    });
}

// ─── Cards & modal ─────────────────────────────────────────────────────────
function displayResearchers(arr){
    const box=document.getElementById('resultsContainer'); box.innerHTML='';
    if(!arr.length){box.innerHTML='<p class="no-results">No matching researchers found.</p>';return;}

    // dedupe by email
    const unique=new Map();
    arr.forEach(r=>{ if(r.email&&!unique.has(r.email)) unique.set(r.email,r); });

    unique.forEach(r=>{
        const card=document.createElement('div'); card.className='researcher-card';
        const list=r.research_areas?.[currentModel]||[];
        const preview=list.length?`
            <div class="research-areas-preview">
                ${list.slice(0,3).map(a=>`<span class="research-area-tag">${a}</span>`).join('')}
                ${list.length>3?`<span class="research-area-tag">+${list.length-3} more</span>`:''}
            </div>`:'' ;

        card.innerHTML=`
            <h3>${r.name||'Unknown'}</h3>
            <p><strong>Title:</strong> ${r.title||'N/A'}</p>
            <p><strong>Email:</strong> ${r.email||'N/A'}</p>
            ${preview}
        `;
        card.addEventListener('click',()=>showResearcherDetails(r));
        box.appendChild(card);
    });
}

function showResearcherDetails(r){
    const modal=document.getElementById('modal-overlay');
    document.getElementById('modalTitle').textContent=r.name||'Details';
    const list=r.research_areas?.[currentModel]||[];
    const body=document.getElementById('modalBody');

    let html=`<div class="researcher-info"><h4>Researcher Information</h4>
        <div class="info-grid">
            <div class="info-item"><span class="info-label">Title</span><span class="info-value">${r.title||'N/A'}</span></div>
            <div class="info-item"><span class="info-label">Email</span><span class="info-value">${r.email||'N/A'}</span></div>`;
    if(r.link?.profile_link) html+=`<div class="info-item"><span class="info-label">University Profile</span><span class="info-value"><a href="${r.link.profile_link}" target="_blank">View</a></span></div>`;
    if(r.link?.google_scholar?.google_scholar_link) html+=`<div class="info-item"><span class="info-label">Google Scholar</span><span class="info-value"><a href="${r.link.google_scholar.google_scholar_link}" target="_blank">View</a></span></div>`;
    if(r.link?.personal_website) html+=`<div class="info-item"><span class="info-label">Website</span><span class="info-value"><a href="${r.link.personal_website}" target="_blank">Visit</a></span></div>`;
    if(r.link?.orcid?.orcid_id) html+=`<div class="info-item"><span class="info-label">ORCID</span><span class="info-value"><a href="${r.link.orcid.orcid_link}" target="_blank">${r.link.orcid.orcid_id}</a></span></div>`;
    html+='</div></div>';

    if(list.length){
        html+=`<div class="research-areas-section"><h4>Research Areas</h4>
               <div class="research-areas-list">${list.map(a=>`<span class="research-area-tag">${a}</span>`).join('')}</div></div>`;
    }
    body.innerHTML=html;
    modal.style.display='flex';
}
function closeModal(){document.getElementById('modal-overlay').style.display='none'}
document.getElementById('modal-overlay').addEventListener('click',e=>{if(e.target===e.currentTarget)closeModal()});
