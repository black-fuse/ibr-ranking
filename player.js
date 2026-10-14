/*
 * IBR leaderboard profiles.
 *
 * Fast path: the leaderboard click handler stores the selected row in
 * sessionStorage before opening this page. This avoids searching pages.
 * Fallback: direct/shared URLs search the selected leaderboard's pages.
 *
 * Once profile links are established, a generated UUID -> player lookup can
 * replace the fallback scan and make shared links instant at any rank.
 */

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

(() => {
  "use strict";

  const BOARD_CONFIG = {
    // Keep these keys in sync with the board IDs used by your leaderboard.
    overall: { label: "Overall standings", path: "data/rankings_overall", type: "paged" },
    tt_all: { label: "All time trials", path: "data/rankings_tt_all", type: "paged" },
    tt_frosthex: { label: "FrostHex time trials", path: "data/rankings_tt_frosthex", type: "paged" },
    tt_frosthexEvent: { label: "FrostHex Event time trials", path: "data/rankings_tt_frosthexEvent", type: "paged" },
    tt_brwc: { label: "BRWC time trials", path: "data/rankings_tt_brwc", type: "paged" },
    tt_bbrl: { label: "BBRL time trials", path: "data/rankings_tt_bbrl", type: "paged" },
    tt_boatlabs: { label: "BoatLabs time trials", path: "data/rankings_tt_boatlabs", type: "paged" },
    tt_wolfnetwork: { label: "WolfNetwork time trials", path: "data/rankings_tt_wolfnetwork", type: "paged" },
    events_all: { label: "All event standings", path: "data/rankings_events", type: "paged" },
    events_boatlabs: { label: "BoatLabs events", path: "data/rankings_events_boatlabs", type: "paged" },
    events_wolfnetwork: { label: "WolfNetwork events", path: "data/rankings_events_wolfnetwork", type: "paged" }
  };

  const $ = (id) => document.getElementById(id);
  const params = new URLSearchParams(window.location.search);
  const boardId = params.get("board") || "";
  const uuid = params.get("uuid") || "";
  const config = BOARD_CONFIG[boardId];
  const storageKey = `ibr-profile:${boardId}:${uuid}`;

  const EVENT_FIELDS = [
    ["events", "Events entered", "integer"],
    ["heats", "Heats raced", "integer"],
    ["wins", "Wins", "integer"],
    ["podiums", "Podiums", "integer"],
    ["top_5", "Top 5 finishes", "integer"],
    ["top_10", "Top 10 finishes", "integer"],
    ["dnfs", "DNFs", "integer"]
  ];
  const TT_FIELDS = [
    ["performances", "Performances", "integer"],
    ["tracks", "Tracks raced", "integer"],
    ["coverage", "Track coverage", "percent"],
    ["track_records", "Track records", "integer"],
    ["podiums", "Podiums", "integer"],
    ["top_5", "Top 5 finishes", "integer"],
    ["top_10", "Top 10 finishes", "integer"]
  ];
  const POSITION_FIELDS = [
    ["average_position", "Average position", "decimal"],
    ["best_position", "Best position", "position"]
  ];

  function showStatus(title, message) {
    $("status").hidden = false;
    $("status").innerHTML = `<div class="loader" aria-hidden="true"></div><h1></h1><p></p>`;
    $("status").querySelector("h1").textContent = title;
    $("status").querySelector("p").textContent = message;
  }

  function showNotFound(message) {
    $("status").hidden = true;
    $("profile").hidden = true;
    $("not-found").hidden = false;
    $("not-found-message").textContent = message;
  }

  function formatValue(value, kind) {
    if (value === null || value === undefined || value === "") return "—";
    const n = Number(value);
    if (!Number.isFinite(n)) return String(value);
    if (kind === "integer") return Math.round(n).toLocaleString();
    if (kind === "decimal") return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
    if (kind === "percent") return `${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
    if (kind === "position") return `#${Math.round(n).toLocaleString()}`;
    if (kind === "time") return `${(n / 1000).toFixed(3)} s`;
    return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }

  function addStat(container, label, value, kind) {
    const card = document.createElement("article");
    card.className = "stat-card";
    const title = document.createElement("span");
    title.className = "stat-label";
    title.textContent = label;
    const output = document.createElement("strong");
    output.className = "stat-value";
    output.textContent = formatValue(value, kind);
    card.append(title, output);
    container.appendChild(card);
  }

  function renderStats(player) {
    const overview = $("overview-stats");
    const details = $("detail-stats");
    overview.replaceChildren();
    details.replaceChildren();

    addStat(overview, "Leaderboard score", player.score, "number");
    if (Object.hasOwn(player, "tt_percentile")) addStat(overview, "TT percentile", player.tt_percentile, "percent");
    if (Object.hasOwn(player, "event_percentile")) addStat(overview, "Event percentile", player.event_percentile, "percent");

    const eventShape = ["events", "heats", "wins", "dnfs"].some((key) => Object.hasOwn(player, key));
    const fields = eventShape ? EVENT_FIELDS : TT_FIELDS;
    for (const [key, label, kind] of fields) {
      if (Object.hasOwn(player, key)) addStat(overview, label, player[key], kind);
    }

    for (const [key, label, kind] of POSITION_FIELDS) {
      if (Object.hasOwn(player, key) && player[key] !== null) addStat(details, label, player[key], kind);
    }
    if (Object.hasOwn(player, "best_time") && player.best_time !== null) {
      addStat(details, "Best time", player.best_time, "time");
    }

    const hasDetails = details.childElementCount > 0;
    $("details-section").hidden = !hasDetails;
  }

  function renderProfile(player) {
    $("status").hidden = true;
    $("not-found").hidden = true;
    $("profile").hidden = false;
    document.title = `${player.name || "Player"} | IBR Rankings`;

    $("board-label").textContent = config.label.toUpperCase();
    $("player-name").textContent = player.name || "Unknown";
    $("player-uuid").textContent = player.uuid || uuid;
    $("player-avatar").src = `https://mc-heads.net/avatar/${encodeURIComponent(player.uuid || uuid)}/88`;
    $("player-avatar").alt = `${player.name || "Player"} Minecraft avatar`;
    $("rank-badge").textContent = `Rank #${formatValue(player.rank, "integer")}`;
    $("score-badge").textContent = `Score ${formatValue(player.score, "number")}`;

    renderStats(player);
    $("back-link").href = `index.html?board=${encodeURIComponent(boardId)}`;
  }

  async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status} loading ${url}`);
    return response.json();
  }

  async function findPlayerFromPages() {
    const index = await fetchJson(`${config.path}/index.json`);
    const totalPages = Number(index.total_pages) || 0;
    if (totalPages === 0) return null;

    // Keep concurrency low so a direct profile link does not flood GitHub Pages.
    // Each batch searches four pages in parallel; most profiles linked from the
    // leaderboard won't use this path because sessionStorage contains the row.
    const batchSize = 4;
    for (let start = 1; start <= totalPages; start += batchSize) {
      const pageNumbers = Array.from(
        { length: Math.min(batchSize, totalPages - start + 1) },
        (_, offset) => start + offset
      );
      const pages = await Promise.all(pageNumbers.map((page) =>
        fetchJson(`${config.path}/page_${page}.json`)
      ));
      for (const rows of pages) {
        const found = rows.find((row) => String(row.uuid).toLowerCase() === uuid.toLowerCase());
        if (found) return found;
      }
    }
    return null;
  }

  // Exported helper for leaderboard script.js:
  // openPlayerProfile(playerRecord, "events_boatlabs")
  window.openPlayerProfile = function (playerRecord, selectedBoard) {
    if (!playerRecord || !playerRecord.uuid || !BOARD_CONFIG[selectedBoard]) {
      console.error("Cannot open profile: player UUID or valid board key is missing.");
      return;
    }
    const key = `ibr-profile:${selectedBoard}:${playerRecord.uuid}`;
    try { sessionStorage.setItem(key, JSON.stringify(playerRecord)); } catch (error) {
      console.warn("Could not cache player profile in sessionStorage:", error);
    }
    const target = new URL("player.html", window.location.href);
    target.searchParams.set("board", selectedBoard);
    target.searchParams.set("uuid", playerRecord.uuid);
    window.location.href = target.href;
  };

  async function init() {
    if (!config || !uuid) {
      showNotFound("The profile URL is missing a valid board or player UUID.");
      return;
    }
    try {
      $("board-label").textContent = config.label.toUpperCase();
      let player = null;
      try {
        const cached = sessionStorage.getItem(storageKey);
        if (cached) {
          const parsed = JSON.parse(cached);
          if (String(parsed.uuid).toLowerCase() === uuid.toLowerCase()) player = parsed;
        }
      } catch (error) {
        console.warn("Could not read cached profile:", error);
      }

      if (!player) {
        showStatus("Loading player profile", "Searching this leaderboard for the player. A direct link may take longer than opening a profile from the leaderboard.");
        player = await findPlayerFromPages();
      }
      if (!player) {
        showNotFound("No entry for this UUID was found in this leaderboard. The player may not have a result on this board yet.");
        return;
      }
      renderProfile(player);
    } catch (error) {
      console.error(error);
      showNotFound("The leaderboard data could not be loaded. Check the board path and make sure its index.json and page files have been published.");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    $("copy-link").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(window.location.href);
        $("copy-link").textContent = "Link copied";
        setTimeout(() => { $("copy-link").textContent = "Copy profile link"; }, 1600);
      } catch {
        window.prompt("Copy this profile link:", window.location.href);
      }
    });
    init();
  });
})();
