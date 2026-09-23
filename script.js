const boards = {
    frosthex: "website/data/rankings_frosthex",
    FrosthexEvent: "website/data/rankings_frosthexEvent",
    brwc: "website/data/rankings_brwc",
    bbrl: "website/data/rankings_bbrl",
    boatlabs: "website/data/rankings_boatlabs",
    all: "website/data/rankings"
};


const backgrounds = document.querySelectorAll(".hero-background img");

let current = 0;

if (backgrounds.length > 0) {

    backgrounds[current].style.opacity = 1;

    setInterval(() => {

        backgrounds[current].style.opacity = 0;

        current = (current + 1) % backgrounds.length;

        backgrounds[current].style.opacity = 1;

    }, 8000);
}



let currentBoard = null;
let currentPage = 0;
let totalPages = 0;
let loading = false;



async function loadRankingIndex(board) {

    const basePath = boards[board];

    const response = await fetch(
        `${basePath}/index.json`
    );

    if (!response.ok) {
        throw new Error(
            `Failed to load ${basePath}/index.json`
        );
    }

    return await response.json();
}



async function loadRankingPage(board, page) {

    const basePath = boards[board];

    const response = await fetch(
        `${basePath}/page_${page}.json`
    );

    if (!response.ok) {
        throw new Error(
            `Failed to load ${basePath}/page_${page}.json`
        );
    }

    return await response.json();
}



function createPlayerWidget(player) {

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

    return widget;
}


async function loadNextPage() {

    if (loading) {
        return;
    }

    if (currentPage >= totalPages) {
        return;
    }

    loading = true;

    try {

        const rankings = await loadRankingPage(
            currentBoard,
            currentPage + 1
        );

        const container =
            document.getElementById("board-container");

        for (const player of rankings) {

            const widget =
                createPlayerWidget(player);

            container.appendChild(widget);
        }

        currentPage++;

    } catch (error) {

        console.error(
            "Failed to load ranking page:",
            error
        );

    } finally {

        loading = false;
    }
}


async function loadRankings(board) {

    currentBoard = board;
    currentPage = 0;
    totalPages = 0;

    const container =
        document.getElementById("board-container");

    container.innerHTML = "";

    try {

        // Get page information
        const index =
            await loadRankingIndex(board);

        totalPages = index.total_pages;

        // Load first page
        await loadNextPage();

    } catch (error) {

        console.error(
            "Failed to load rankings:",
            error
        );

        container.innerHTML =
            "<p>Failed to load rankings.</p>";
    }
}

// detect when user reaches bottom
window.addEventListener("scroll", () => {

    const scrollPosition =
        window.innerHeight + window.scrollY;

    const pageHeight =
        document.documentElement.scrollHeight;

    // Start loading slightly before the actual bottom
    const threshold = 500;

    if (
        scrollPosition >= pageHeight - threshold
        && !loading
    ) {

        loadNextPage();
    }
});


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
        player.name =
            await mojangUuidToUsername(player.uuid);
    }

    return player;
}


async function mojangUuidToUsername(uuid) {

    const cleanUuid =
        uuid.replace(/-/g, "");

    const response = await fetch(
        `https://sessionserver.mojang.com/session/minecraft/profile/${cleanUuid}`
    );

    if (!response.ok) {
        return uuid;
    }

    const data =
        await response.json();

    return data.name;
}


const buttons =
    document.querySelectorAll(".board-button");

buttons.forEach(button => {

    button.addEventListener("click", () => {

        buttons.forEach(button => {
            button.classList.remove("active");
        });

        button.classList.add("active");

        const board =
            button.dataset.board;

        loadRankings(board);
    });
});




loadRankings("all");