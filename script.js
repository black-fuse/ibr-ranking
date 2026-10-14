
const boards = {
    overall: {
        type: "paged",
        path: "website/data/rankings_overall"
    },

    tt_all: {
        type: "paged",
        path: "website/data/rankings_tt_all"
    },
    tt_frosthex: {
        type: "paged",
        path: "website/data/rankings_tt_frosthex"
    },
    tt_frosthexEvent: {
        type: "paged",
        path: "website/data/rankings_tt_frosthexEvent"
    },
    tt_brwc: {
        type: "paged",
        path: "website/data/rankings_tt_brwc"
    },
    tt_bbrl: {
        type: "paged",
        path: "website/data/rankings_tt_bbrl"
    },
    tt_boatlabs: {
        type: "paged",
        path: "website/data/rankings_tt_boatlabs"
    },
    tt_wolfnetwork: {
        type: "paged",
        path: "website/data/rankings_tt_wolfnetwork"
    },

    events_all: {
        type: "paged",
        path: "website/data/rankings_events"
    },
    events_boatlabs: {
        type: "paged",
        path: "website/data/rankings_events_boatlabs"
    },
    events_wolfnetwork: {
        type: "paged",
        path: "website/data/rankings_events_wolfnetwork"
    }
};


const backgrounds =
    document.querySelectorAll(".hero-background img");

let currentBackground = 0;

if (backgrounds.length > 0) {
    backgrounds[currentBackground].style.opacity = 1;

    setInterval(() => {
        backgrounds[currentBackground].style.opacity = 0;

        currentBackground =
            (currentBackground + 1) % backgrounds.length;

        backgrounds[currentBackground].style.opacity = 1;
    }, 8000);
}


let currentBoard = null;
let currentPage = 0;
let totalPages = 0;
let loading = false;

// Changes every time a different leaderboard is selected.
// Prevents old requests from affecting the new leaderboard.
let boardRequestId = 0;


async function fetchJSON(path) {
    const response = await fetch(path);

    if (!response.ok) {
        throw new Error(
            `Failed to load ${path}: HTTP ${response.status}`
        );
    }

    return response.json();
}


async function loadRankingIndex(board) {
    const config = boards[board];
    return fetchJSON(`${config.path}/index.json`);
}


async function loadRankingPage(board, page) {
    const config = boards[board];
    return fetchJSON(`${config.path}/page_${page}.json`);
}


function createPlayerWidget(player, boardID) {
    const widget = document.createElement("div");
    widget.className = "player-widget";

    const rank = document.createElement("div");
    rank.className = "player-rank";

    const skin = document.createElement("img");
    skin.className = "player-skin";
    skin.alt = `${player.name}'s Minecraft skin`;
    skin.loading = "lazy";
    skin.src =
        "https://mc-heads.net/avatar/" +
        encodeURIComponent(player.uuid) +
        "/50";

    // Use the exported rank if present. Otherwise, calculate a tier
    // from the player's leaderboard position.
    const position = Number(player.rank);
    const tier = getTier(
        Number.isFinite(position) && position > 0 ? position : Infinity
    );

    rank.textContent = player.rank ?? "—";
    rank.classList.add(tier);

    const name = document.createElement("div");
    name.className = "player-name";
    name.textContent = player.name ?? player.uuid ?? "Unknown player";

    const score = document.createElement("div");
    score.className = "player-score";
    score.textContent =
        `${Number(player.score ?? 0).toLocaleString()} points`;

    widget.append(rank, skin, name, score);

    widget.addEventListener("click", () => {
        openPlayerProfile(player, boardID);
    });

    return widget;
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


function renderPlayers(players, container, boardID) {
    if (!Array.isArray(players)) {
        throw new Error("The leaderboard JSON is not an array.");
    }

    const fragment = document.createDocumentFragment();

    for (const player of players) {
        fragment.appendChild(createPlayerWidget(player, boardID));
    }

    container.appendChild(fragment);
}



async function loadNextPage() {
    if (loading || !currentBoard) return;
    if (currentPage >= totalPages) return;

    const requestId = boardRequestId;
    const board = currentBoard;
    const page = currentPage + 1;

    loading = true;

    try {
        const rankings = await loadRankingPage(board, page);

        // Ignore a response if the user switched boards while waiting.
        if (requestId !== boardRequestId) return;

        const container =
            document.getElementById("board-container");

        renderPlayers(rankings, container, board);
        currentPage = page;

    } catch (error) {
        if (requestId === boardRequestId) {
            console.error("Failed to load ranking page:", error);
            showError("Failed to load the next page.");
        }
    } finally {
        if (requestId === boardRequestId) {
            loading = false;
        }
    }
}


function showError(message) {
    const container =
        document.getElementById("board-container");

    container.replaceChildren();

    const error = document.createElement("p");
    error.textContent = message;
    container.appendChild(error);
}


async function loadRankings(board) {
    if (!boards[board]) {
        showError("Unknown leaderboard.");
        return;
    }

    const requestId = ++boardRequestId;
    const config = boards[board];

    currentBoard = board;
    currentPage = 0;
    totalPages = 0;
    loading = false;

    const container =
        document.getElementById("board-container");

    container.replaceChildren();

    const loadingMessage = document.createElement("p");
    loadingMessage.textContent = "Loading...";
    container.appendChild(loadingMessage);

    try {
        if (config.type === "single") {
            const rankings = await fetchJSON(config.path);

            if (requestId !== boardRequestId) return;

            container.replaceChildren();
            renderPlayers(rankings, container);
            return;
        }

        const index = await loadRankingIndex(board);

        if (requestId !== boardRequestId) return;

        totalPages = Number(index.total_pages) || 0;
        container.replaceChildren();

        if (totalPages === 0) {
            const empty = document.createElement("p");
            empty.textContent = "No rankings available yet.";
            container.appendChild(empty);
            return;
        }

        await loadNextPage();

    } catch (error) {
        if (requestId !== boardRequestId) return;

        console.error("Failed to load rankings:", error);
        showError(
            "Failed to load rankings. Check that the data files exist."
        );
    }
}


// Infinite scroll is only used for paginated leaderboards.
window.addEventListener("scroll", () => {
    if (!currentBoard) return;
    if (boards[currentBoard]?.type !== "paged") return;

    const scrollPosition =
        window.innerHeight + window.scrollY;

    const pageHeight =
        document.documentElement.scrollHeight;

    if (scrollPosition >= pageHeight - 500 && !loading) {
        loadNextPage();
    }
});


const buttons =
    document.querySelectorAll(".board-button");

buttons.forEach(button => {
    button.addEventListener("click", () => {
        buttons.forEach(item => item.classList.remove("active"));
        button.classList.add("active");

        loadRankings(button.dataset.board);
    });
});

function openPlayerProfile(player, boardId) {
    if (!player?.uuid) return;

    try {
        sessionStorage.setItem(
            `ibr-profile:${boardId}:${player.uuid}`,
            JSON.stringify(player)
        );
    } catch (error) {
        console.warn("Could not cache profile data:", error);
    }

    const url = new URL("player.html", window.location.href);
    url.searchParams.set("board", boardId);
    url.searchParams.set("uuid", player.uuid);

    window.location.href = url.href;
}


// Start with the combined leaderboard.
loadRankings("overall");
