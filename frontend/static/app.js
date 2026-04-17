const API = '';
let curEvent = null;
let cardPollTimer = null;

// ============================================================
// NAVIGATION
// ============================================================
function showPage(id) {
    clearTimers();
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}
function clearTimers() { if (cardPollTimer) { clearInterval(cardPollTimer); cardPollTimer = null; } }
function goHome() { clearTimers(); curEvent = null; showPage('page-home'); loadEvents(); }
function goCourse() { showPage('page-course'); refreshCoursePage(); }
function goResults() { verifMode = false; showPage('page-results'); loadResults(); }

// ============================================================
// PAGE 1: DASHBOARD
// ============================================================
async function loadEvents() {
    const events = await api('GET', '/api/events');
    const el = document.getElementById('events-list');

    if (!events.length) {
        el.innerHTML = '<p class="hint" style="text-align:center;padding:2rem">Aucune course. Cree-en une ci-dessus.</p>';
        return;
    }

    el.innerHTML = events.map(ev => {
        const s = ev.stats;
        const pct = ev.photo_count > 0 ? Math.round(ev.processed_count / ev.photo_count * 100) : 0;
        const cardCount = ev.cards ? ev.cards.length : 0;

        let statusCls = 'status-idle', statusText = 'Vide';
        if (ev.photo_count > 0 && ev.processed_count === 0) { statusCls = 'status-ready'; statusText = 'Pret'; }
        else if (ev.pending_count > 0 && ev.processed_count > 0) { statusCls = 'status-processing'; statusText = 'En cours'; }
        else if (ev.photo_count > 0 && ev.pending_count === 0) { statusCls = 'status-done'; statusText = 'Termine'; }

        return `
            <div class="event-card" onclick="openEvent(${ev.id})">
                <div class="ev-header">
                    <div>
                        <h3>${esc(ev.name)}</h3>
                        <span class="ev-date">${ev.date}</span>
                    </div>
                    <span class="status-badge ${statusCls}">${statusText}</span>
                </div>
                <div class="ev-body">
                    <span>${ev.photo_count} photos</span>
                    <span>${cardCount} carte(s)</span>
                    ${pct > 0 ? `<div class="progress-bar progress-sm"><div class="progress-fill" style="width:${pct}%"></div></div>` : ''}
                    ${s && s.unique_bibs ? `<span class="ev-bibs">${s.unique_bibs} dossard(s)</span>` : ''}
                </div>
                <div class="ev-actions">
                    <button class="btn" onclick="event.stopPropagation(); openEvent(${ev.id})">Ouvrir</button>
                    <button class="btn btn-danger" onclick="event.stopPropagation(); delEvent(${ev.id})">Supprimer</button>
                </div>
            </div>`;
    }).join('');
}

async function openEvent(id) {
    curEvent = await api('GET', `/api/events/${id}`);
    goCourse();
}

async function delEvent(id) {
    if (!confirm('Supprimer cette course et toutes ses photos ?')) return;
    await api('DELETE', `/api/events/${id}`);
    loadEvents();
}

// ============================================================
// PAGE 2: CREER COURSE
// ============================================================
document.getElementById('cr-blur').addEventListener('input', e => {
    document.getElementById('cr-blur-val').textContent = e.target.value;
});
document.getElementById('cr-yolo').addEventListener('input', e => {
    document.getElementById('cr-yolo-val').textContent = e.target.value + '%';
});

// Sample bib drop zone
const crSampleDrop = document.getElementById('cr-sample-drop');
let crSampleFile = null;
crSampleDrop.addEventListener('dragover', e => { e.preventDefault(); crSampleDrop.classList.add('dragover'); });
crSampleDrop.addEventListener('dragleave', () => crSampleDrop.classList.remove('dragover'));
crSampleDrop.addEventListener('drop', e => {
    e.preventDefault(); crSampleDrop.classList.remove('dragover');
    if (e.dataTransfer.files.length) setCrSample(e.dataTransfer.files[0]);
});
crSampleDrop.addEventListener('click', () => document.getElementById('cr-sample-input').click());
document.getElementById('cr-sample-input').addEventListener('change', e => {
    if (e.target.files.length) setCrSample(e.target.files[0]);
});
function setCrSample(file) {
    crSampleFile = file;
    const preview = document.getElementById('cr-sample-preview');
    const txt = document.getElementById('cr-sample-text');
    preview.src = URL.createObjectURL(file);
    preview.style.display = ''; txt.style.display = 'none';
}

document.getElementById('form-create-event').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('cr-name').value;
    const date = document.getElementById('cr-date').value;

    const ev = await api('POST', '/api/events', { name, date });
    if (ev.detail) { alert('Erreur: ' + ev.detail); return; }

    await api('PUT', `/api/events/${ev.id}/config`, {
        blur_threshold: parseFloat(document.getElementById('cr-blur').value),
        yolo_confidence: parseInt(document.getElementById('cr-yolo').value) / 100,
        bib_min_digits: parseInt(document.getElementById('cr-bib-min').value),
        bib_max_digits: parseInt(document.getElementById('cr-bib-max').value),
    });

    if (crSampleFile) {
        const fd = new FormData();
        fd.append('file', crSampleFile);
        await fetch(`${API}/api/events/${ev.id}/sample-bib`, { method: 'POST', body: fd });
        crSampleFile = null;
    }

    document.getElementById('form-create-event').reset();
    document.getElementById('cr-sample-preview').style.display = 'none';
    document.getElementById('cr-sample-text').style.display = '';
    document.getElementById('cr-blur-val').textContent = '40';
    document.getElementById('cr-yolo-val').textContent = '35%';

    curEvent = await api('GET', `/api/events/${ev.id}`);
    goCourse();
});

// ============================================================
// PAGE 3: VUE COURSE
// ============================================================
function refreshCoursePage() {
    if (!curEvent) return;
    document.getElementById('course-title').textContent = curEvent.name;
    renderCourseStats();
    renderCourseCards();
    refreshProcessBtn();
    startCardPoll();
}

function renderCourseStats() {
    const ev = curEvent;
    const s = ev.stats;
    const el = document.getElementById('course-stats');
    el.innerHTML = `
        <div class="cs-item"><span class="cs-num">${ev.photo_count}</span><span class="cs-label">Photos</span></div>
        <div class="cs-item"><span class="cs-num">${ev.processed_count}</span><span class="cs-label">Traitees</span></div>
        <div class="cs-item"><span class="cs-num">${ev.cards ? ev.cards.length : 0}</span><span class="cs-label">Cartes</span></div>
        ${s ? `<div class="cs-item cs-bon"><span class="cs-num">${s.unique_bibs}</span><span class="cs-label">Dossards</span></div>` : ''}
    `;
}

function renderCourseCards() {
    const el = document.getElementById('course-cards');
    if (!curEvent || !curEvent.cards || !curEvent.cards.length) {
        el.innerHTML = '<p class="hint" style="padding:1rem;text-align:center">Aucune carte importee. Ajoute une carte pour commencer.</p>';
        return;
    }

    el.innerHTML = curEvent.cards.map(c => {
        const pct = c.total_expected > 0 ? Math.round(c.photo_count / c.total_expected * 100) : (c.status === 'done' ? 100 : 0);
        const statusMap = {
            'pending': ['ij-active', 'En attente'],
            'importing': ['ij-active', `Import ${c.photo_count}/${c.total_expected}`],
            'done': ['ij-done', `${c.photo_count} photos`],
            'stopped': ['ij-stopped', `Arrete (${c.photo_count})`],
            'error': ['ij-error', 'Erreur'],
        };
        const [cls, statusText] = statusMap[c.status] || ['', c.status];

        return `
            <div class="card-item ${cls}">
                <div class="ij-header">
                    <span class="ij-label">${esc(c.name)}</span>
                    <span class="ij-status">${statusText}</span>
                    <button class="btn-x" onclick="deleteCard(${c.id})" title="Supprimer">x</button>
                </div>
                ${c.total_expected > 0 ? `<div class="progress-bar progress-sm"><div class="progress-fill" style="width:${pct}%"></div></div>` : ''}
                ${c.source_path ? `<span class="hint">${esc(c.source_path)}</span>` : ''}
            </div>`;
    }).join('');
}

function startCardPoll() {
    if (!curEvent) return;
    const hasActive = curEvent.cards && curEvent.cards.some(c => c.status === 'importing' || c.status === 'pending');
    if (hasActive && !cardPollTimer) {
        cardPollTimer = setInterval(async () => {
            curEvent = await api('GET', `/api/events/${curEvent.id}`);
            renderCourseCards();
            renderCourseStats();
            refreshProcessBtn();
            const still = curEvent.cards.some(c => c.status === 'importing' || c.status === 'pending');
            if (!still) { clearInterval(cardPollTimer); cardPollTimer = null; }
        }, 3000);
    }
}

async function deleteCard(cardId) {
    if (!confirm('Supprimer cette carte et ses photos ?')) return;
    await api('DELETE', `/api/cards/${cardId}`);
    curEvent = await api('GET', `/api/events/${curEvent.id}`);
    renderCourseCards();
    renderCourseStats();
    refreshProcessBtn();
}

// Settings page
document.getElementById('cfg-blur').addEventListener('input', e => {
    document.getElementById('cfg-blur-val').textContent = e.target.value;
});
document.getElementById('cfg-yolo').addEventListener('input', e => {
    document.getElementById('cfg-yolo-val').textContent = e.target.value + '%';
});

async function saveConfig() {
    if (!curEvent) return;
    curEvent = await api('PUT', `/api/events/${curEvent.id}/config`, {
        blur_threshold: parseFloat(document.getElementById('cfg-blur').value),
        yolo_confidence: parseInt(document.getElementById('cfg-yolo').value) / 100,
        bib_min_digits: parseInt(document.getElementById('cfg-bib-min').value),
        bib_max_digits: parseInt(document.getElementById('cfg-bib-max').value),
    });
    alert('Parametres sauvegardes !');
    goCourse();
}

// ============================================================
// PAGE 3c: AJOUTER CARTE
// ============================================================
document.getElementById('form-folder').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!curEvent) return;
    const pathInput = document.getElementById('folder-path');
    const path = pathInput.value.trim();
    if (!path) return;

    const res = await api('POST', `/api/events/${curEvent.id}/import-folder`, { folder_path: path });
    if (res.detail) { alert('Erreur: ' + res.detail); return; }
    pathInput.value = '';
    curEvent = await api('GET', `/api/events/${curEvent.id}`);
    goCourse();
});

document.getElementById('file-input').addEventListener('change', async (e) => {
    if (!curEvent || !e.target.files.length) return;
    const files = e.target.files;
    const total = files.length;

    const card = await api('POST', `/api/events/${curEvent.id}/cards`, { name: `Upload (${total} fichiers)` });

    for (let i = 0; i < total; i += 20) {
        const fd = new FormData();
        for (let j = i; j < Math.min(i + 20, total); j++) fd.append('files', files[j]);
        await fetch(`${API}/api/events/${curEvent.id}/photos?card_id=${card.id}`, { method: 'POST', body: fd });
    }

    e.target.value = '';
    curEvent = await api('GET', `/api/events/${curEvent.id}`);
    goCourse();
});

// ============================================================
// PROCESSING
// ============================================================
function showStopBtn(show) {
    document.getElementById('btn-stop').style.display = show ? '' : 'none';
}

async function refreshProcessBtn() {
    if (!curEvent) return;
    const st = await api('GET', `/api/events/${curEvent.id}/process/status`);
    const btn = document.getElementById('btn-process');
    const btnR = document.getElementById('btn-results');
    const btnReset = document.getElementById('btn-reset');
    showStopBtn(false);
    if (st.total === 0) {
        btn.textContent = 'Aucune photo'; btn.disabled = true;
        btnR.style.display = 'none'; btnReset.style.display = 'none';
    } else if (st.pending === 0) {
        btn.textContent = 'Tout est traite !'; btn.disabled = true;
        btnR.style.display = ''; btnReset.style.display = '';
    } else if (st.processed > 0) {
        btn.textContent = `Traiter (${st.pending} restantes)`; btn.disabled = false;
        btnR.style.display = ''; btnReset.style.display = '';
    } else {
        btn.textContent = `Lancer le traitement (${st.pending} photos)`; btn.disabled = false;
        btnR.style.display = 'none'; btnReset.style.display = 'none';
    }
}

async function stopCurrentEvent() {
    if (!curEvent) return;
    await api('POST', `/api/events/${curEvent.id}/stop`);
    showStopBtn(false);
    setTimeout(async () => {
        curEvent = await api('GET', `/api/events/${curEvent.id}`);
        refreshCoursePage();
    }, 2000);
}

async function resetCurrentEvent() {
    if (!curEvent) return;
    if (!confirm('Remettre a zero tout le traitement ? Les photos sont conservees.')) return;
    await api('POST', `/api/events/${curEvent.id}/reset`);
    curEvent = await api('GET', `/api/events/${curEvent.id}`);
    document.getElementById('process-progress').style.display = 'none';
    refreshCoursePage();
}

async function launchProcess() {
    if (!curEvent) return;
    const btn = document.getElementById('btn-process');
    btn.disabled = true; btn.textContent = 'Traitement...';
    showStopBtn(true);

    await api('POST', `/api/events/${curEvent.id}/process`);

    const prog = document.getElementById('process-progress');
    const fill = document.getElementById('process-fill');
    const text = document.getElementById('process-text');
    prog.style.display = 'block';

    const poll = async () => {
        const st = await api('GET', `/api/events/${curEvent.id}/process/status`);
        const pct = st.total > 0 ? Math.round(st.processed / st.total * 100) : 0;
        fill.style.width = pct + '%';
        text.textContent = `${st.processed}/${st.total} traitees...`;
        if (st.pending > 0) setTimeout(poll, 2000);
        else {
            fill.style.width = '100%';
            text.textContent = 'Traitement termine !';
            btn.textContent = 'Tout est traite !';
            showStopBtn(false);
            curEvent = await api('GET', `/api/events/${curEvent.id}`);
            refreshCoursePage();
        }
    };
    setTimeout(poll, 2000);
}

// ============================================================
// PAGE 4: RESULTS
// ============================================================
let allPhotos = [];

async function loadResults() {
    if (!curEvent) return;
    document.getElementById('results-title').textContent = curEvent.name + ' — Resultats';

    const photos = await api('GET', `/api/events/${curEvent.id}/photos?processed_only=true`);
    allPhotos = photos;

    const flou = [], coupe = [], mauvais = [], sansBib = [];
    const bibs = {};

    for (const p of photos) {
        const d = p.detections[0];
        if (!d) { mauvais.push(p); continue; }
        const cls = d.validated_class || d.classification;
        const bib = d.validated_bib || d.bib_number;
        if (cls === 'flou') flou.push(p);
        else if (cls === 'coupe') coupe.push(p);
        else if (bib) { (bibs[bib] = bibs[bib] || []).push(p); }
        else if (cls === 'mauvais') mauvais.push(p);
        else sansBib.push(p);
    }

    const bibKeys = Object.keys(bibs).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
    const confirmedBibs = bibKeys.filter(k => bibs[k].length >= 2);
    const singleBibs = bibKeys.filter(k => bibs[k].length === 1);
    const singlePhotos = singleBibs.flatMap(k => bibs[k]);
    const confirmedCount = confirmedBibs.reduce((s, k) => s + bibs[k].length, 0);

    // Count already validated
    const validatedCount = photos.filter(p => {
        const d = p.detections[0];
        return d && d.validated_class;
    }).length;

    document.getElementById('results-stats').innerHTML = `
        <span><strong>${photos.length}</strong> photos</span>
        <span class="badge badge-bon">${confirmedCount} confirmees (${confirmedBibs.length})</span>
        <span class="badge badge-incertain">${singlePhotos.length} packs uniques</span>
        <span class="badge badge-flou">${flou.length} floues</span>
        <span class="badge badge-coupe">${coupe.length} coupees</span>
        <span class="badge badge-mauvais">${mauvais.length + sansBib.length} rejetees</span>
        ${validatedCount > 0 ? `<span class="hint">${validatedCount} deja validees</span>` : ''}
    `;

    let html = '';
    if (confirmedBibs.length) {
        html += '<div class="section-label section-ok">Dossards confirmes (2+ photos)</div><div class="folders-grid">';
        for (const bib of confirmedBibs) html += folderCard(`#${bib}`, bibs[bib].length, photoUrl(bibs[bib][0]), `openFolder('bib','${bib}')`);
        html += '</div>';
    }
    if (singlePhotos.length) {
        html += '<div class="section-label section-warn">Packs uniques — a verifier</div><div class="folders-grid">';
        html += folderCard('Packs uniques', singlePhotos.length, photoUrl(singlePhotos[0]), `openFolder('singles','')`, 'incertain');
        html += '</div>';
    }
    if (sansBib.length) {
        html += '<div class="section-label section-warn">Sans dossard</div><div class="folders-grid">';
        html += folderCard('Sans dossard', sansBib.length, photoUrl(sansBib[0]), `openFolder('sansbib','')`, 'incertain');
        html += '</div>';
    }
    if (flou.length || coupe.length || mauvais.length) {
        html += '<div class="section-label section-bad">Ecartees</div><div class="folders-grid">';
        if (flou.length) html += folderCard('Floues', flou.length, photoUrl(flou[0]), `openFolder('flou','')`, 'flou');
        if (coupe.length) html += folderCard('Coupees', coupe.length, photoUrl(coupe[0]), `openFolder('coupe','')`, 'coupe');
        if (mauvais.length) html += folderCard('Rejetees', mauvais.length, photoUrl(mauvais[0]), `openFolder('mauvais','')`, 'mauvais');
        html += '</div>';
    }
    document.getElementById('folders-list').innerHTML = html || '<p class="hint">Aucun resultat.</p>';
}

function folderCard(title, count, thumb, onclick, badgeCls) {
    const badge = badgeCls ? `<span class="badge badge-${badgeCls}" style="margin-left:0.3rem">${badgeCls}</span>` : '';
    return `
        <div class="folder-card" onclick="${onclick}">
            ${thumb ? `<img class="folder-thumb" src="${thumb}">` : '<div class="folder-icon">?</div>'}
            <h3>${esc(title)}${badge}</h3>
            <span class="folder-count">${count} photo(s)</span>
        </div>`;
}

function photoUrl(p) {
    if (!p || !curEvent) return '';
    const base = `/uploads/${curEvent.id}/${p.filepath.split('/').pop()}`;
    return base + '?t=' + (p._rotated || p.id);
}

// ============================================================
// VERIF MODE — Smart verification flow
// ============================================================
let verifMode = false;
let verifQueue = [];      // All photos in smart order
let verifTotal = 0;       // Total at start
let verifDone = 0;        // How many validated
let verifPhases = { confirmed: 0, singles: 0, noBib: 0 };  // Counts per phase

function startVerifMode() {
    if (!allPhotos.length) return;

    verifMode = true;
    verifQueue = [];
    verifDone = 0;

    // Build groups from current data
    const bibs = {};
    const noBibPhotos = [];

    for (const p of allPhotos) {
        const d = p.detections[0];
        if (!d) continue;
        // Skip already validated photos
        if (d.validated_class) continue;
        const cls = d.classification;
        const bib = d.bib_number;
        if (cls === 'flou' || cls === 'coupe' || cls === 'mauvais') continue; // skip rejected
        if (bib) {
            (bibs[bib] = bibs[bib] || []).push(p);
        } else {
            noBibPhotos.push(p);
        }
    }

    const bibKeys = Object.keys(bibs).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
    const confirmedBibs = bibKeys.filter(k => bibs[k].length >= 2);
    const singleBibs = bibKeys.filter(k => bibs[k].length === 1);

    // PHASE 1: Confirmed bibs — grouped by dossard, sorted by score desc within each
    const phase1 = [];
    for (const bib of confirmedBibs) {
        const sorted = bibs[bib].sort((a, b) => {
            const sa = (a.detections[0] || {}).overall_score || 0;
            const sb = (b.detections[0] || {}).overall_score || 0;
            return sb - sa;
        });
        for (const p of sorted) {
            p._verifPhase = 1;
            p._verifBibGroup = bib;
            p._verifGroupSize = sorted.length;
            phase1.push(p);
        }
    }

    // PHASE 2: Single bibs — sorted by score desc
    const phase2 = [];
    for (const bib of singleBibs) {
        const p = bibs[bib][0];
        p._verifPhase = 2;
        p._verifBibGroup = bib;
        p._verifGroupSize = 1;
        phase2.push(p);
    }
    phase2.sort((a, b) => {
        const sa = (a.detections[0] || {}).overall_score || 0;
        const sb = (b.detections[0] || {}).overall_score || 0;
        return sb - sa;
    });

    // PHASE 3: No bib photos
    const phase3 = [];
    for (const p of noBibPhotos) {
        p._verifPhase = 3;
        p._verifBibGroup = null;
        p._verifGroupSize = 0;
        phase3.push(p);
    }

    verifQueue = [...phase1, ...phase2, ...phase3];
    verifTotal = verifQueue.length;
    verifPhases = { confirmed: phase1.length, singles: phase2.length, noBib: phase3.length };

    if (!verifQueue.length) {
        alert('Rien a verifier ! Toutes les photos sont deja traitees.');
        return;
    }

    // Setup viewer for verif mode
    viewerPhotos = verifQueue;
    viewerIdx = 0;
    viewerHistory = [];
    viewerTitle = 'Verification';

    document.getElementById('viewer-back-btn').onclick = () => { verifMode = false; goResults(); };
    document.getElementById('verif-phases').style.display = '';
    updateVerifUI();

    showPage('page-viewer');
    vShow();
}

function updateVerifUI() {
    if (!verifMode) {
        document.getElementById('verif-phases').style.display = 'none';
        return;
    }

    // Progress
    const pct = verifTotal > 0 ? Math.round(verifDone / verifTotal * 100) : 0;
    document.getElementById('verif-progress').style.width = pct + '%';

    // Count remaining per phase
    let r1 = 0, r2 = 0, r3 = 0;
    for (const p of viewerPhotos) {
        if (p._verifPhase === 1) r1++;
        else if (p._verifPhase === 2) r2++;
        else if (p._verifPhase === 3) r3++;
    }

    // Phase indicators
    const cur = viewerPhotos[viewerIdx];
    const curPhase = cur ? cur._verifPhase : 0;

    const vp1 = document.getElementById('vp-1');
    const vp2 = document.getElementById('vp-2');
    const vp3 = document.getElementById('vp-3');

    vp1.className = 'vp-item' + (curPhase === 1 ? ' vp-active' : '') + (r1 === 0 ? ' vp-done' : '');
    vp2.className = 'vp-item' + (curPhase === 2 ? ' vp-active' : '') + (r2 === 0 ? ' vp-done' : '');
    vp3.className = 'vp-item' + (curPhase === 3 ? ' vp-active' : '') + (r3 === 0 ? ' vp-done' : '');

    document.getElementById('vp-1-count').textContent = r1 > 0 ? r1 : '';
    document.getElementById('vp-2-count').textContent = r2 > 0 ? r2 : '';
    document.getElementById('vp-3-count').textContent = r3 > 0 ? r3 : '';
}

// ============================================================
// PAGE 5: VIEWER
// ============================================================
let viewerPhotos = [], viewerIdx = 0, viewerTitle = '';
let viewerHistory = [];

function openFolder(type, val) {
    verifMode = false;
    document.getElementById('verif-phases').style.display = 'none';
    document.getElementById('viewer-back-btn').onclick = () => goResults();

    viewerPhotos = [];
    let singleBibSet = null;
    if (type === 'singles') {
        const bibCounts = {};
        for (const p of allPhotos) { const d = p.detections[0]; if (!d) continue; const bib = d.validated_bib || d.bib_number; if (bib) bibCounts[bib] = (bibCounts[bib] || 0) + 1; }
        singleBibSet = new Set(Object.keys(bibCounts).filter(k => bibCounts[k] === 1));
    }

    for (const p of allPhotos) {
        const d = p.detections[0];
        if (!d) { if (type === 'mauvais') viewerPhotos.push(p); continue; }
        const cls = d.validated_class || d.classification;
        const bib = d.validated_bib || d.bib_number;
        if (type === 'bib' && bib === val) viewerPhotos.push(p);
        else if (type === 'singles' && bib && singleBibSet.has(bib)) viewerPhotos.push(p);
        else if (type === 'flou' && cls === 'flou') viewerPhotos.push(p);
        else if (type === 'coupe' && cls === 'coupe') viewerPhotos.push(p);
        else if (type === 'mauvais' && cls === 'mauvais' && !bib) viewerPhotos.push(p);
        else if (type === 'sansbib' && cls !== 'flou' && cls !== 'coupe' && cls !== 'mauvais' && !bib) viewerPhotos.push(p);
    }
    viewerTitle = type === 'bib' ? 'Dossard #' + val : type === 'singles' ? 'Packs uniques' : type === 'flou' ? 'Floues' : type === 'coupe' ? 'Coupees' : type === 'mauvais' ? 'Rejetees' : 'Sans dossard';
    viewerIdx = 0;
    viewerHistory = [];
    showPage('page-viewer');
    vShow();
}

function vShow() {
    if (!viewerPhotos.length) {
        if (verifMode) {
            verifMode = false;
            document.getElementById('verif-phases').style.display = 'none';
            goResults();
            return;
        }
        goResults();
        return;
    }
    viewerIdx = Math.max(0, Math.min(viewerIdx, viewerPhotos.length - 1));

    const p = viewerPhotos[viewerIdx];
    const d = p.detections[0] || {};
    const cls = d.validated_class || d.classification || '?';
    const bib = d.validated_bib || d.bib_number || '';

    // Title
    if (verifMode) {
        const phase = p._verifPhase;
        const phaseLabel = phase === 1 ? 'Confirme' : phase === 2 ? 'Unique' : 'Sans dossard';
        const groupInfo = p._verifBibGroup ? ` — #${p._verifBibGroup}` : '';
        document.getElementById('viewer-title').textContent = `Verification: ${phaseLabel}${groupInfo}`;
    } else {
        document.getElementById('viewer-title').textContent = viewerTitle;
    }

    document.getElementById('viewer-counter').textContent = `${viewerIdx + 1}/${viewerPhotos.length}`;
    document.getElementById('viewer-bib').textContent = bib ? `#${bib}` : 'Pas de dossard';
    document.getElementById('viewer-score').textContent = d.overall_score != null ? `Score: ${Math.round(d.overall_score * 100)}/100` : '';
    document.getElementById('viewer-file').textContent = p.filename;

    // Confidence indicator (verif mode)
    const confEl = document.getElementById('viewer-confidence');
    if (verifMode && p._verifPhase) {
        if (p._verifPhase === 1) {
            confEl.textContent = 'CONFIRME';
            confEl.className = 'viewer-confidence vc-high';
        } else if (p._verifPhase === 2) {
            confEl.textContent = 'A VERIFIER';
            confEl.className = 'viewer-confidence vc-medium';
        } else {
            confEl.textContent = 'MANUEL';
            confEl.className = 'viewer-confidence vc-low';
        }
        confEl.style.display = '';
    } else {
        confEl.style.display = 'none';
    }

    const badge = document.getElementById('viewer-badge');
    badge.textContent = cls;
    badge.className = 'badge badge-' + cls;

    const bibInput = document.getElementById('viewer-bib-input');
    bibInput.value = bib;
    bibInput.focus();
    bibInput.select();

    const img = document.getElementById('viewer-img');
    img.src = photoUrl(p);
    img.onload = () => drawBbox(p, d, img);

    if (verifMode) updateVerifUI();
}

function drawBbox(p, d, img) {
    const canvas = document.getElementById('viewer-canvas');
    const wrap = document.getElementById('viewer-img-wrap');
    const ir = img.getBoundingClientRect();
    const wr = wrap.getBoundingClientRect();
    canvas.width = img.naturalWidth; canvas.height = img.naturalHeight;
    canvas.style.width = ir.width + 'px'; canvas.style.height = ir.height + 'px';
    canvas.style.left = (ir.left - wr.left) + 'px'; canvas.style.top = (ir.top - wr.top) + 'px';
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!d.bbox_w) return;
    const sx = img.naturalWidth / (p.width || img.naturalWidth);
    const sy = img.naturalHeight / (p.height || img.naturalHeight);
    const clsC = d.validated_class || d.classification;
    ctx.strokeStyle = clsC === 'bon' ? '#34d399' : clsC === 'incertain' ? '#fbbf24' : '#f87171';
    ctx.lineWidth = 4;
    ctx.strokeRect(d.bbox_x * sx, d.bbox_y * sy, d.bbox_w * sx, d.bbox_h * sy);
    const bibT = d.validated_bib || d.bib_number;
    if (bibT) { ctx.fillStyle = ctx.strokeStyle; ctx.font = `bold ${Math.max(28, canvas.width * 0.035)}px sans-serif`; ctx.fillText('#' + bibT, d.bbox_x * sx, d.bbox_y * sy - 10); }
}

function vNav(dir) {
    viewerIdx += dir;
    if (viewerIdx < 0) viewerIdx = viewerPhotos.length - 1;
    if (viewerIdx >= viewerPhotos.length) viewerIdx = 0;
    vShow();
}

async function vAct(cls) {
    if (!viewerPhotos.length) return;
    const p = viewerPhotos[viewerIdx];
    const d = p.detections[0];
    if (!d) { viewerPhotos.splice(viewerIdx, 1); vShow(); return; }
    const body = { validated_class: cls };
    const bibVal = document.getElementById('viewer-bib-input').value.trim();
    if (bibVal) body.validated_bib = bibVal;

    const prevClass = d.validated_class || d.classification;
    const prevBib = d.validated_bib || d.bib_number;

    await api('PUT', `/api/detections/${d.id}/validate`, body);
    d.validated = true; d.validated_class = cls;
    if (bibVal) d.validated_bib = bibVal;

    viewerHistory.push({ photo: p, index: viewerIdx, prevClass, prevBib });
    viewerPhotos.splice(viewerIdx, 1);

    if (verifMode) verifDone++;

    document.getElementById('viewer-img').classList.add('viewer-flash');
    setTimeout(() => document.getElementById('viewer-img').classList.remove('viewer-flash'), 250);

    setTimeout(() => {
        if (!viewerPhotos.length) {
            if (verifMode) {
                verifMode = false;
                document.getElementById('verif-phases').style.display = 'none';
            }
            goResults();
            return;
        }
        if (viewerIdx >= viewerPhotos.length) viewerIdx = 0;
        vShow();
    }, 150);
}

async function vUndo() {
    if (!viewerHistory.length) return;
    const last = viewerHistory.pop();
    const d = last.photo.detections[0];
    if (!d) return;
    await api('PUT', `/api/detections/${d.id}/validate`, { validated_class: last.prevClass, validated_bib: last.prevBib || null });
    d.validated_class = last.prevClass;
    d.validated_bib = last.prevBib;
    viewerPhotos.splice(last.index, 0, last.photo);
    viewerIdx = last.index;
    if (verifMode) verifDone = Math.max(0, verifDone - 1);
    vShow();
}

async function vRotate() {
    if (!viewerPhotos.length || !curEvent) return;
    const p = viewerPhotos[viewerIdx];
    const res = await api('POST', `/api/photos/${p.id}/rotate`);
    if (res.width) { p.width = res.width; p.height = res.height; }
    p._rotated = Date.now();
    const img = document.getElementById('viewer-img');
    img.src = '';
    img.src = photoUrl(p);
    img.onload = () => drawBbox(p, p.detections[0] || {}, img);
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (!document.getElementById('page-viewer').classList.contains('active')) return;

    switch (e.key) {
        case 'a': case 'A': e.preventDefault(); vAct('mauvais'); return;
        case 'z': case 'Z': e.preventDefault(); vUndo(); return;
        case 'r': case 'R': e.preventDefault(); vRotate(); return;
        case 'Enter': e.preventDefault(); vAct('bon'); return;
    }

    if (document.activeElement === document.getElementById('viewer-bib-input')) {
        if (e.key === 'ArrowLeft') { e.preventDefault(); vNav(-1); return; }
        if (e.key === 'ArrowRight') { e.preventDefault(); vNav(1); return; }
        return;
    }

    if (e.key >= '0' && e.key <= '9') {
        const input = document.getElementById('viewer-bib-input');
        input.value = '';
        input.focus();
        return;
    }

    switch (e.key) {
        case 'ArrowLeft': e.preventDefault(); vNav(-1); break;
        case 'ArrowRight': e.preventDefault(); vNav(1); break;
    }
});

// ============================================================
// ZOOM ON HOVER
// ============================================================
(function() {
    const ZOOM = 3, SIZE = 250;
    const imgEl = document.getElementById('viewer-img');
    const zoomEl = document.getElementById('viewer-zoom');

    imgEl.addEventListener('mouseenter', () => { if (imgEl.naturalWidth) zoomEl.style.display = 'block'; });
    imgEl.addEventListener('mouseleave', () => { zoomEl.style.display = 'none'; });
    imgEl.addEventListener('mousemove', (e) => {
        if (!imgEl.naturalWidth) return;
        zoomEl.style.backgroundImage = `url(${imgEl.src})`;
        zoomEl.style.backgroundSize = `${imgEl.clientWidth * ZOOM}px ${imgEl.clientHeight * ZOOM}px`;
        const rect = imgEl.getBoundingClientRect();
        const wrap = imgEl.parentElement.getBoundingClientRect();
        const x = e.clientX - rect.left, y = e.clientY - rect.top;
        zoomEl.style.left = (rect.left - wrap.left) + x - SIZE / 2 + 'px';
        zoomEl.style.top = (rect.top - wrap.top) + y - SIZE / 2 + 'px';
        zoomEl.style.backgroundPosition = `${-(x * ZOOM - SIZE / 2)}px ${-(y * ZOOM - SIZE / 2)}px`;
    });
})();

// ============================================================
// UTILS
// ============================================================
async function api(method, path, body) {
    const opts = { method };
    if (body) { opts.headers = { 'Content-Type': 'application/json' }; opts.body = JSON.stringify(body); }
    const res = await fetch(API + path, opts);
    return res.json();
}

function esc(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// ============================================================
// INIT
// ============================================================
loadEvents();
