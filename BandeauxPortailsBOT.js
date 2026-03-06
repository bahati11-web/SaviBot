/*
╔════════════════════════╗
║  BandeauxPortailsBOT   ║
╚════════════════════════╝
*/
// Version 2.0     
// Script pour ajouter des portails depuis une catégorie avec son Bot      
// Testé pour Vikidia, soyez prudent sur les autres wikis      
      
// <nowiki>      
(function () {
    'use strict';
    if (window.BandeauxPortailsBOT) return;
    window.BandeauxPortailsBOT = true;

    if (
        mw.config.get('wgCanonicalSpecialPageName') !== 'Blankpage' ||
        !location.pathname.includes('BandeauxPortailsBOT')
    ) return;

    const api = new mw.Api();
    const params = { category: '', portalName: '', pauseMs: 1000 };
    let stopFlag = false, pauseFlag = false, totalPages = 0, processedPages = 0;

    const container = document.createElement('div');
    container.style.padding = '15px';
    container.style.borderRadius = '12px';
    container.style.boxShadow = '0 4px 20px rgba(0,0,0,0.2)';
    container.style.background = 'linear-gradient(145deg,#fdfdfd,#e6f0ff)';
    container.style.fontFamily = 'Consolas, monospace';
    container.style.marginBottom = '20px';
    container.style.maxWidth = '600px';

    container.innerHTML = `
        <h2 style="margin:0 0 10px 0; color:#1a1aff;">BandeauxPortailsBOT</h2>
        <div style="margin-bottom:8px;">
            <label>Catégorie : </label><input id="bp_category" style="width:60%; padding:4px; border-radius:4px; border:1px solid #ccc;">
        </div>
        <div style="margin-bottom:8px;">
            <label>Portail : </label><input id="bp_portal" style="width:60%; padding:4px; border-radius:4px; border:1px solid #ccc;">
        </div>
        <div style="margin-bottom:12px;">
            <label>Pause (ms) : </label><input id="bp_pause" type="number" value="1000" style="width:80px; padding:4px; border-radius:4px; border:1px solid #ccc;">
        </div>
        <div style="display:flex; gap:8px; margin-bottom:12px;">
            <button id="bp_start" style="flex:1; padding:6px; border:none; border-radius:6px; background:#1a1aff; color:white; font-weight:bold; cursor:pointer;">Lancer</button>
            <button id="bp_pause_btn" style="flex:1; padding:6px; border:none; border-radius:6px; background:#ff9933; color:white; font-weight:bold; cursor:pointer;">Pause</button>
            <button id="bp_stop" style="flex:1; padding:6px; border:none; border-radius:6px; background:#ff3333; color:white; font-weight:bold; cursor:pointer;">Stop</button>
        </div>
        <div style="margin-bottom:6px;">
            <div id="bp_progress" style="height:12px; background:#ddd; border-radius:6px; overflow:hidden;">
                <div style="width:0; height:100%; background:#1a1aff;" id="bp_progress_bar"></div>
            </div>
        </div>
        <div id="bp_log" style="margin-top:10px; max-height:250px; overflow:auto; background:#fefefe; padding:8px; border-radius:6px; border:1px solid #ccc;"></div>
    `;

    document.getElementById('mw-content-text').prepend(container);
    const logDiv = container.querySelector('#bp_log');
    const progressBar = container.querySelector('#bp_progress_bar');

    function log(msg, type = 'info') {
        const color = type === 'error' ? 'red' : type === 'success' ? 'green' : '#444';
        logDiv.innerHTML += `<span style="color:${color};">${msg}</span><br>`;
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    function updateProgress() {
        if (totalPages === 0) return;
        const pct = Math.round((processedPages / totalPages) * 100);
        progressBar.style.width = pct + '%';
    }

    function normaliser(liste) {
        return new Set(liste.map(v => v.trim().toLowerCase()).filter(Boolean));
    }

    async function getCategoryMembers(cat) {
        let members = [], cmcontinue;
        do {
            const data = await api.get({
                action: 'query',
                list: 'categorymembers',
                cmtitle: 'Category:' + cat,
                cmlimit: 'max',
                cmcontinue
            });
            members = members.concat(data.query.categorymembers || []);
            cmcontinue = data.continue ? data.continue.cmcontinue : null;
        } while (cmcontinue);
        return members;
    }

    async function getPageText(title) {
        const data = await api.get({
            action: 'query',
            prop: 'revisions',
            titles: title,
            rvslots: 'main',
            rvprop: 'content'
        });
        const page = Object.values(data.query.pages)[0];
        return page.revisions ? page.revisions[0].slots.main['*'] : '';
    }

    function modifierPortail(texte, portailNom) {
        const portailLower = portailNom.trim().toLowerCase();
        const regex = /\{\{\s*portail\s*(\|?[\s\S]*?)?\}\}/gi;
        let match, found = false;

        while ((match = regex.exec(texte)) !== null) {
            let currentParams = match[1] ? match[1].split('|').map(p => p.trim()).filter(Boolean) : [];
            const paramsSet = new Set(currentParams.map(p => p.toLowerCase()));
            if (paramsSet.has(portailLower)) return { text: texte, modified: false };
            currentParams.push(portailNom.trim());
            texte = texte.replace(match[0], '{{Portail|' + currentParams.join('|') + '}}');
            found = true;
        }

        if (!found) {
            const ajout = '{{Portail|' + portailNom.trim() + '}}\n';
            const catMatch = texte.match(/\[\[Category:[^\]]+\]\]/i);
            texte = catMatch ? texte.slice(0, catMatch.index) + ajout + texte.slice(catMatch.index) : texte.trimEnd() + '\n' + ajout;
        }

        return { text: texte, modified: true };
    }

    async function savePage(title, text) {
        return api.postWithToken('csrf', {
            action: 'edit',
            title: title,
            text: text,
            summary: 'Bot : ajout du portail ' + params.portalName,
            minor: true
        });
    }

    async function traiterPage(title) {
        if (stopFlag) return;
        while (pauseFlag) await new Promise(r => setTimeout(r, 200));

        try {
            const texte = await getPageText(title);
            if (!texte) return;

            const result = modifierPortail(texte, params.portalName);
            if (!result.modified) {
                log('Déjà correct sur : ' + title, 'success');
            } else {
                await savePage(title, result.text);
                log('Portail ajouté sur : ' + title, 'success');
            }
        } catch (e) {
            log('Erreur sur ' + title + ' : ' + e.message, 'error');
        } finally {
            processedPages++;
            updateProgress();
        }
    }

    async function main() {
        stopFlag = false; pauseFlag = false; processedPages = 0;
        log('Lancement du traitement...', 'info');

        const pages = await getCategoryMembers(params.category);
        totalPages = pages.length;

        for (const p of pages) {
            if (stopFlag) break;
            await traiterPage(p.title);
        }

        log('Traitement terminé !', 'info');
    }

    container.querySelector('#bp_start').onclick = function () {
        params.category = container.querySelector('#bp_category').value.trim();
        params.portalName = container.querySelector('#bp_portal').value.trim();
        params.pauseMs = parseInt(container.querySelector('#bp_pause').value, 10) || 1000;
        main();
    };

    container.querySelector('#bp_pause_btn').onclick = function () {
        pauseFlag = !pauseFlag;
        log(pauseFlag ? 'Pause' : 'Reprise', 'info');
        this.style.background = pauseFlag ? '#3399ff' : '#ff9933';
    };

    container.querySelector('#bp_stop').onclick = function () {
        stopFlag = true;
        log('Arrêt demandé', 'info');
    };
})();
// </nowiki>
