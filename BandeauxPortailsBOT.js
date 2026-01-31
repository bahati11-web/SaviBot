// BandeauxPortailsBOT.js
// Auteur : Bahati11
// Domaine public
// Alerte compatibilité : Testé sur Vikidia, prudence sur autres wikis
// Script pour ajouter des portails aux pages d'une catégorie 

(function () {
    if (window.BandeauxPortailsBOT) return;
    window.BandeauxPortailsBOT = true;

    let params = { category: '', portalName: '', pauseMs: 1000 };
    let stopFlag = false;
    let pauseFlag = false;

    const container = document.createElement('div');
    container.style.padding = '10px';
    container.style.border = '2px solid #444';
    container.style.margin = '10px'; 
    container.style.backgroundColor = '#f0f0f0';
    container.style.fontFamily = 'monospace';
    container.innerHTML = `
        <h3>BandeauxPortailsBOT</h3>
        <label>Catégorie : <input type="text" id="bp_category" value="${params.category}"></label><br>
        <label>Portail à ajouter : <input type="text" id="bp_portal" value="${params.portalName}"></label><br>
        <label>Pause (ms) : <input type="number" id="bp_pause" value="${params.pauseMs}"></label><br><br>
        <button id="bp_start">Lancer</button>
        <button id="bp_pause_btn">Pause</button>
        <button id="bp_stop">Stop</button>
        <div id="bp_log" style="margin-top:10px; max-height:300px; overflow:auto; background:#fff; padding:5px; border:1px solid #ccc;"></div>
    `;
    document.body.prepend(container);

    const logDiv = container.querySelector('#bp_log');
    const log = (msg) => {
        console.log(msg);
        logDiv.innerHTML += msg + '<br>';
        logDiv.scrollTop = logDiv.scrollHeight;
    };

    async function getCategoryMembers(catName) {
        const res = await fetch(`/w/api.php?action=query&list=categorymembers&cmtitle=Category:${encodeURIComponent(catName)}&cmlimit=max&format=json&origin=*`);
        const data = await res.json();
        return data.query.categorymembers || [];
    }

    async function getPageText(title) {
        const res = await fetch(`/w/api.php?action=query&prop=revisions&titles=${encodeURIComponent(title)}&rvslots=*&rvprop=content&format=json&origin=*`);
        const data = await res.json();
        const pages = data.query.pages;
        const pageId = Object.keys(pages)[0];
        return pages[pageId].revisions[0].slots.main['*'] || '';
    }

    async function savePage(title, text, summary) {
        const tokenRes = await fetch(`/w/api.php?action=query&meta=tokens&type=csrf&format=json&origin=*`);
        const tokenData = await tokenRes.json();
        const token = tokenData.query.tokens.csrftoken;
        const formData = new FormData();
        formData.append('action', 'edit');
        formData.append('title', title);
        formData.append('text', text);
        formData.append('summary', summary);
        formData.append('token', token);
        formData.append('format', 'json');
        const res = await fetch(`/w/api.php`, { method: 'POST', body: formData });
        const data = await res.json();
        return data;
    }

    function modifyPortal(text, portalName) {
        const portalLower = portalName.toLowerCase();
        const pattern = /\{\{\s*portal\s*(\|[\s\S]*?)?\}\}/gi;
        let modified = false;

        text = text.replace(pattern, (match, paramsStr) => {
            let params = paramsStr ? paramsStr.split('|').map(p => p.trim()).filter(Boolean) : [];
            const paramsLower = params.map(p => p.toLowerCase());
            if (paramsLower.includes(portalLower)) return match;
            params.push(portalName);
            modified = true;
            return `{{Portal|${params.join('|')}}}`;
        });

        if (!pattern.test(text) && !text.toLowerCase().includes(`{{portal|${portalLower}}}`)) {
            const catMatch = text.match(/\[\[Category:[^\]]+\]\]/i);
            const ajout = `{{Portal|${portalName}}}\n`;
            if (catMatch) {
                const index = catMatch.index;
                text = text.slice(0, index) + ajout + text.slice(index);
            } else {
                text += '\n' + ajout;
            }
            modified = true;
        }

        return { text, modified };
    }

    async function traiterPage(pageTitle) {
        if (stopFlag) return;
        while (pauseFlag) await new Promise(r => setTimeout(r, 200));
        try {
            let texte = await getPageText(pageTitle);
            if (/{{\s*Disambiguation\s*}}/i.test(texte)) return;
            const { text: newText, modified } = modifyPortal(texte, params.portalName);
            if (!modified || newText.trim() === texte.trim()) {
                log(`Portail déjà correct : ${pageTitle}`);
                return;
            }
            await savePage(pageTitle, newText, `Bot: + portal ${params.portalName}`);
            log(`Portail ajouté : ${pageTitle}`);
            await new Promise(r => setTimeout(r, params.pauseMs));
        } catch (e) {
            log(`Erreur sur ${pageTitle} : ${e}`);
        }
    }

    async function main() {
        stopFlag = false;
        pauseFlag = false;
        const members = await getCategoryMembers(params.category);
        for (const page of members) {
            if (stopFlag) break;
            await traiterPage(page.title);
        }
        log('Traitement terminé');
    }

    container.querySelector('#bp_start').addEventListener('click', () => {
        params.category = container.querySelector('#bp_category').value.trim();
        params.portalName = container.querySelector('#bp_portal').value.trim();
        params.pauseMs = parseInt(container.querySelector('#bp_pause').value.trim()) || 1000;
        main();
    });

    container.querySelector('#bp_pause_btn').addEventListener('click', () => {
        pauseFlag = !pauseFlag;
        container.querySelector('#bp_pause_btn').innerText = pauseFlag ? 'Reprendre' : 'Pause';
        log(pauseFlag ? 'Pausé' : 'Repris');
    });

    container.querySelector('#bp_stop').addEventListener('click', () => {
        stopFlag = true;
        log('Arrêt demandé');
    });

})();
