const boards = {
    frosthex: "website/data/rankings_frosthex.json",
    brwc: "website/data/rankings_brwc.json",
    bbrl: "website/data/rankings_bbrl.json",
    boatlabs: "website/data/rankings_boatlabs.json",
    all: "website/data/rankings.json"
};

const backgrounds = document.querySelectorAll(".hero-background img");

let current = 0;
backgrounds[current].style.opacity = 1;

setInterval(() => {
    backgrounds[current].style.opacity = 0;

    current = (current + 1) % backgrounds.length;

    backgrounds[current].style.opacity = 1;
}, 8000);

async function loadRankings(board) {

    const response = await fetch(boards[board]);

    if (!response.ok) {
        throw new Error(`Failed to load ${boards[board]}`);
    }

    const rankings = await response.json();

    const container = document.getElementById("board-container");

    container.innerHTML = "";

    for (const player of rankings) {

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

        skin.src =
            "https://mc-heads.net/avatar/"
            + player.uuid
            + "/50";

        widget.appendChild(rank);
        widget.appendChild(skin);
        widget.appendChild(name);
        widget.appendChild(score);

        container.appendChild(widget);
    }
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


async function fixPlayerName(player) {

    if (player.name === player.uuid) {
        player.name = await mojangUuidToUsername(player.uuid);
    }

    return player;
}


async function mojangUuidToUsername(uuid) {

    const cleanUuid = uuid.replace(/-/g, "");

    const response = await fetch(
        `https://sessionserver.mojang.com/session/minecraft/profile/${cleanUuid}`
    );

    if (!response.ok) {
        return uuid;
    }

    const data = await response.json();

    return data.name;
}


// Board buttons
const buttons = document.querySelectorAll(".board-button");

buttons.forEach(button => {

    button.addEventListener("click", () => {

        // Remove active state from all buttons
        buttons.forEach(button => {
            button.classList.remove("active");
        });

        // Activate clicked button
        button.classList.add("active");

        // Load selected leaderboard
        const board = button.dataset.board;

        loadRankings(board);
    });
});


// Load default board
loadRankings("frosthex");