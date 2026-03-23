// IPL Predict — main.js

let tossDecision = 'bat';
let modelChart = null;
let h2hChart = null;

// ── Tab switching ──────────────────────────────────────
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + tab).classList.add('active');

        if (tab === 'stats') loadSeasonStats();
        if (tab === 'players') loadPlayers();
    });
});

// ── Toss toggle ────────────────────────────────────────
document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        tossDecision = btn.dataset.value;
    });
});

// ── Update toss options when teams change ──────────────
function updateTossOptions() {
    const t1 = document.getElementById('team1-select').value;
    const t2 = document.getElementById('team2-select').value;
    const sel = document.getElementById('toss-winner-select');
    sel.innerHTML = '<option value="">Select Team</option>';
    if (t1) sel.innerHTML += `<option value="${t1}">${t1}</option>`;
    if (t2) sel.innerHTML += `<option value="${t2}">${t2}</option>`;
}

document.getElementById('team1-select').addEventListener('change', updateTossOptions);
document.getElementById('team2-select').addEventListener('change', updateTossOptions);

// ── Predict ────────────────────────────────────────────
document.getElementById('predict-btn').addEventListener('click', async () => {
    const team1 = document.getElementById('team1-select').value;
    const team2 = document.getElementById('team2-select').value;
    const venue = document.getElementById('venue-select').value;
    const tossWinner = document.getElementById('toss-winner-select').value;

    if (!team1 || !team2) { alert('Please select both teams!'); return; }
    if (team1 === team2) { alert('Please select two different teams!'); return; }

    const btn = document.getElementById('predict-btn');
    btn.classList.add('loading');
    btn.textContent = 'Predicting...';

    try {
        const res = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team1, team2, venue, toss_winner: tossWinner, toss_decision: tossDecision })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        showResults(data, team1, team2);
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        btn.classList.remove('loading');
        btn.textContent = '⚡ Predict Winner';
    }
});

function showResults(data, team1, team2) {
    document.getElementById('predictor-form-view').style.display = 'none';
    document.getElementById('predictor-results-view').style.display = 'block';

    // Winner
    document.getElementById('winner-name').textContent = data.predicted_winner;

    // Probability bar
    const t1Prob = data.ensemble.team1_prob;
    const t2Prob = data.ensemble.team2_prob;
    const t1Short = team1.split(' ').slice(-1)[0];
    const t2Short = team2.split(' ').slice(-1)[0];

    document.getElementById('t1-name-bar').textContent = t1Short;
    document.getElementById('t2-name-bar').textContent = t2Short;
    document.getElementById('t1-bar').style.width = t1Prob + '%';
    document.getElementById('t2-bar').style.width = t2Prob + '%';
    document.getElementById('t1-pct').textContent = t1Prob + '%';
    document.getElementById('t2-pct').textContent = t2Prob + '%';

    // Model accuracies
    document.getElementById('lr-acc').textContent = data.logistic_regression.accuracy + '%';
    document.getElementById('rf-acc').textContent = data.random_forest.accuracy + '%';

    // Chart
    if (modelChart) modelChart.destroy();
    const ctx = document.getElementById('model-chart').getContext('2d');
    modelChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Log. Regression', 'Random Forest', 'Ensemble'],
            datasets: [
                {
                    label: t1Short,
                    data: [data.logistic_regression.team1_prob, data.random_forest.team1_prob, data.ensemble.team1_prob],
                    backgroundColor: 'rgba(249,115,22,0.7)',
                    borderRadius: 4
                },
                {
                    label: t2Short,
                    data: [data.logistic_regression.team2_prob, data.random_forest.team2_prob, data.ensemble.team2_prob],
                    backgroundColor: 'rgba(59,130,246,0.7)',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#64748b', font: { family: 'Poppins', size: 11 } } }
            },
            scales: {
                x: { ticks: { color: '#64748b', font: { family: 'Poppins' } }, grid: { display: false } },
                y: {
                    ticks: { color: '#64748b', callback: v => v + '%', font: { family: 'Poppins' } },
                    grid: { color: '#f1f5f9' },
                    max: 100
                }
            }
        }
    });

    // H2H
    const h2h = data.head_to_head;
    document.getElementById('h2h-t1-wins').textContent = h2h.team1_wins || 0;
    document.getElementById('h2h-t2-wins').textContent = h2h.team2_wins || 0;
    document.getElementById('h2h-t1-name').textContent = t1Short;
    document.getElementById('h2h-t2-name').textContent = t2Short;
    document.getElementById('h2h-total').textContent = `of ${h2h.total || 0} matches`;
}

// ── Back button ────────────────────────────────────────
document.getElementById('back-btn').addEventListener('click', () => {
    document.getElementById('predictor-results-view').style.display = 'none';
    document.getElementById('predictor-form-view').style.display = 'block';
});

// ── Season Stats (simple table instead of chart) ───────
let seasonLoaded = false;
async function loadSeasonStats() {
    if (seasonLoaded) return;
    try {
        const res = await fetch('/api/season_stats');
        const data = await res.json();

        const rows = data.map(d => `
            <tr>
                <td>${d.season}</td>
                <td class="champion-team">${d.champion}</td>
                <td>${d.matches}</td>
            </tr>
        `).join('');

        document.getElementById('champions-list').innerHTML = `
            <table class="champions-table">
                <thead>
                    <tr><th>Season</th><th>Champion</th><th>Matches</th></tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
        seasonLoaded = true;
    } catch (e) {
        document.getElementById('champions-list').innerHTML = '<p style="color:#64748b;font-size:0.9rem">Failed to load data.</p>';
    }
}

// ── Team Stats ─────────────────────────────────────────
document.getElementById('team-stats-select').addEventListener('change', async function () {
    const team = this.value;
    if (!team) return;
    try {
        const res = await fetch(`/api/team_stats/${encodeURIComponent(team)}`);
        const d = await res.json();
        document.getElementById('team-stats-result').innerHTML = `
            <div class="stat-boxes">
                <div class="stat-box"><div class="num">${d.total_matches}</div><div class="lbl">Matches</div></div>
                <div class="stat-box"><div class="num">${d.wins}</div><div class="lbl">Wins</div></div>
                <div class="stat-box"><div class="num">${d.win_rate}%</div><div class="lbl">Win Rate</div></div>
                <div class="stat-box"><div class="num">${d.titles}</div><div class="lbl">Titles</div></div>
            </div>
        `;
    } catch (e) {
        document.getElementById('team-stats-result').innerHTML = '<p style="color:#64748b">Failed to load.</p>';
    }
});

// ── H2H Stats ──────────────────────────────────────────
document.getElementById('h2h-btn').addEventListener('click', async () => {
    const t1 = document.getElementById('h2h-team1').value;
    const t2 = document.getElementById('h2h-team2').value;
    if (!t1 || !t2 || t1 === t2) { alert('Select two different teams'); return; }

    try {
        const res = await fetch('/api/head_to_head', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team1: t1, team2: t2 })
        });
        const d = await res.json();

        document.getElementById('h2h-summary').innerHTML = `
            <div class="h2h-summary-row">
                <div class="h2h-team"><div class="h2h-wins">${d.team1_wins}</div><div class="h2h-name">${t1.split(' ').slice(-1)[0]}</div></div>
                <div class="h2h-of">of ${d.total} matches</div>
                <div class="h2h-team"><div class="h2h-wins">${d.team2_wins}</div><div class="h2h-name">${t2.split(' ').slice(-1)[0]}</div></div>
            </div>
        `;

        const chartEl = document.getElementById('h2h-chart');
        chartEl.style.display = 'block';
        if (h2hChart) h2hChart.destroy();

        const seasons = d.season_data || [];
        h2hChart = new Chart(chartEl.getContext('2d'), {
            type: 'line',
            data: {
                labels: seasons.map(s => s.season),
                datasets: [
                    {
                        label: t1.split(' ').slice(-1)[0],
                        data: seasons.map(s => s.team1_wins),
                        borderColor: '#f97316',
                        backgroundColor: 'rgba(249,115,22,0.1)',
                        fill: true, tension: 0.4, pointRadius: 4
                    },
                    {
                        label: t2.split(' ').slice(-1)[0],
                        data: seasons.map(s => s.team2_wins),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59,130,246,0.1)',
                        fill: true, tension: 0.4, pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: '#64748b', font: { family: 'Poppins' } } } },
                scales: {
                    x: { ticks: { color: '#64748b', font: { family: 'Poppins' } }, grid: { display: false } },
                    y: { ticks: { color: '#64748b', font: { family: 'Poppins' }, stepSize: 1 }, grid: { color: '#f1f5f9' } }
                }
            }
        });
    } catch (e) {
        alert('Failed to load H2H data.');
    }
});

// ── Players ────────────────────────────────────────────
async function loadPlayers() {
    const grid = document.getElementById('players-grid');
    if (grid.dataset.loaded) return;

    try {
        const res = await fetch('/api/top_players');
        const d = await res.json();

        function makeTable(title, rows, valKey, valLabel) {
            const rowsHtml = rows.map((r, i) => `
                <tr>
                    <td class="rank-cell">${i + 1}</td>
                    <td class="player-name">${r.name}</td>
                    <td class="stat-val">${r[valKey].toLocaleString()}</td>
                </tr>
            `).join('');
            return `
                <div class="card">
                    <h2 class="card-title">${title}</h2>
                    <table class="player-table">
                        <thead><tr><th>#</th><th>Player</th><th>${valLabel}</th></tr></thead>
                        <tbody>${rowsHtml}</tbody>
                    </table>
                </div>
            `;
        }

        grid.innerHTML =
            makeTable('🏏 Top Run Scorers', d.top_batsmen, 'runs', 'Runs') +
            makeTable('🎳 Top Wicket Takers', d.top_bowlers, 'wickets', 'Wickets');

        grid.dataset.loaded = '1';
    } catch (e) {
        grid.innerHTML = '<p style="color:#64748b;grid-column:span 2">Failed to load player data.</p>';
    }
}
