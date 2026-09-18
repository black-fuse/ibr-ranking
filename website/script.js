async function loadRankings() {

    const response = await fetch("data/rankings.json");
    const rankings = await response.json();

    const container = document.getElementById("board-container");

    container.innerHTML = "";

    rankings.forEach(player => {

        const widget = document.createElement("div");
        widget.className = "player-widget";

        const rank = document.createElement("div");
        rank.className = "player-rank";

        const skin = document.createElement("img");
        skin.className = "player-skin";

        const name = document.createElement("div");
        name.className = "player-name";

        const score = document.createElement("div");
        score.className = "player-score";

        const tier = getTier(player.rank);

        rank.textContent = player.rank;
        rank.classList.add(tier);
        name.textContent = player.name;
        score.textContent = `${player.score} points`;

        // Temporary skin placeholder
        skin.src = "https://mc-heads.net/avatar/" + player.uuid + "/50";

        widget.appendChild(rank);
        widget.appendChild(skin);
        widget.appendChild(name);
        widget.appendChild(score);

        container.appendChild(widget);
    });
}

function getTier(rank) {

    if (rank <= 20) return "netherite";
    if (rank <= 50) return "diamond";
    if (rank <= 100) return "emerald";
    if (rank <= 300) return "gold";
    if (rank <= 1000) return "iron";
    if (rank <= 10000) return "copper";

    return "stone";
}

loadRankings();