// BandeauxPortailsBOT.js | Version 1.2 | Bahati11  
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
    ) {  
        return;  
    }  

    var api = new mw.Api();  
    var params = { category: '', portalName: '', pauseMs: 1000 };  
    var stopFlag = false;  
    var pauseFlag = false;  

    var container = document.createElement('div');  
    container.style.padding = '10px';  
    container.style.border = '2px solid #444';  
    container.style.background = '#f0f0f0';  
    container.style.fontFamily = 'monospace';  

    container.innerHTML = `  
        <h3>BandeauxPortailsBOT</h3>  
        Catégorie : <input id="bp_category"><br>  
        Portail : <input id="bp_portal"><br>  
        Pause (ms) : <input id="bp_pause" type="number" value="1000"><br><br>  
        <button id="bp_start">Lancer</button>  
        <button id="bp_pause_btn">Pause</button>  
        <button id="bp_stop">Stop</button>  
        <div id="bp_log" style="margin-top:10px; max-height:300px; overflow:auto; background:#fff; padding:5px;"></div>  
    `;  

    document.getElementById('mw-content-text').prepend(container);  

    var logDiv = container.querySelector('#bp_log');  
    function log(msg) {  
        logDiv.innerHTML += msg + '<br>';  
        logDiv.scrollTop = logDiv.scrollHeight;  
    }  

    function normaliser(liste) {  
        return new Set(liste.map(v => v.trim().toLowerCase()).filter(Boolean));  
    }  

    async function getCategoryMembers(cat) {  
        const data = await api.get({  
            action: 'query',  
            list: 'categorymembers',  
            cmtitle: 'Category:' + cat,  
            cmlimit: 'max',  
            cmnamespace: 0  
        });  
        return data.query.categorymembers || [];  
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
        const texteNet = texte.replace(/<!--[\s\S]*?-->/g, '');  
        const regex = /\{\{\s*portail\s*(\|[\s\S]*?)?\}\}|\{\{\s*portail\s+([^\|\}]+)\s*\}\}/gi;  
        let matchFound = false;  

        texte = texte.replace(regex, (match, p1, p2) => {  
            let paramsList = [];  
            if (p1) {  
                paramsList = p1.split('|').map(p => p.trim()).filter(Boolean);  
            } else if (p2) {  
                paramsList = [p2.trim()];  
            }  
            const paramsNorm = normaliser(paramsList);  
            if (paramsNorm.has(portailLower)) {  
                matchFound = true;  
                return match;  
            }  
            paramsList.push(portailNom.trim());  
            matchFound = true;  
            return '{{portail|' + paramsList.join('|') + '}}';  
        });  

        if (matchFound) {  
            return { text: texte, modified: true };  
        }  

        const ajout = '{{portail|' + portailNom.trim() + '}}\n';  
        const catMatch = texte.match(/\[\[Category:[^\]]+\]\]/i);  

        if (catMatch) {  
            texte = texte.slice(0, catMatch.index) + ajout + texte.slice(catMatch.index);  
        } else {  
            texte = texte.trimEnd() + '\n' + ajout;  
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
                log('Déjà correct : ' + title);  
                return;  
            }  

            await savePage(title, result.text);  
            log('Portail ajouté : ' + title);  
            await new Promise(r => setTimeout(r, params.pauseMs));  
        } catch (e) {  
            log('Erreur sur ' + title + ' : ' + e.message);  
        }  
    }  

    async function main() {  
        stopFlag = false;  
        pauseFlag = false;  
        log('Lancement du traitement');  

        const pages = await getCategoryMembers(params.category);  
        for (const p of pages) {  
            if (stopFlag) break;  
            await traiterPage(p.title);  
        }  

        log('Traitement terminé');  
    }  

    container.querySelector('#bp_start').onclick = function () {  
        params.category = container.querySelector('#bp_category').value.trim();  
        params.portalName = container.querySelector('#bp_portal').value.trim();  
        params.pauseMs = parseInt(container.querySelector('#bp_pause').value, 10) || 1000;  
        main();  
    };  

    container.querySelector('#bp_pause_btn').onclick = function () {  
        pauseFlag = !pauseFlag;  
        log(pauseFlag ? 'Pause' : 'Reprise');  
    };  

    container.querySelector('#bp_stop').onclick = function () {  
        stopFlag = true;  
        log('Arrêt demandé');  
    };  
})();  
// </nowiki>