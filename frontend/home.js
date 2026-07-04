// WanderSoul — Home Page Logic

const FALLBACK_IMG = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Hampi_virupaksha_temple.jpg/900px-Hampi_virupaksha_temple.jpg";

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const res = await fetch("/api/destinations");
        if (!res.ok) throw new Error("API unavailable");
        const data = await res.json();
        const destinations = data.destinations || [];

        // Update destination count in boarding strip
        const statEl = document.getElementById("stat-destinations");
        if (statEl) statEl.textContent = `${data.count || destinations.length} Destinations`;

        if (!destinations.length) return;

        // ── Hero image: use first destination with a valid image_url ──
        const heroImg = document.getElementById("hero-img");
        if (heroImg) {
            const heroSrc = destinations[0].image_url || FALLBACK_IMG;
            heroImg.src = heroSrc;
            heroImg.alt = `${destinations[0].name} — ${destinations[0].region}`;
        }

        // ── Editorial grid: pick up to 5 featured destinations ──
        const grid = document.getElementById("editorial-grid");
        if (!grid) return;

        // Spread picks across the dataset for variety
        const picks = pickFeatured(destinations, 5);
        grid.innerHTML = picks.map((d, i) => buildCard(d, i)).join("");

    } catch (err) {
        console.warn("Home page data load failed:", err.message);
        // Silently fall back — hero stays blank, grid keeps its placeholder
        const heroImg = document.getElementById("hero-img");
        if (heroImg && !heroImg.src) heroImg.src = FALLBACK_IMG;
    }
});

/**
 * Pick up to `n` destinations spread across the full list for variety.
 * @param {Array} list
 * @param {number} n
 * @returns {Array}
 */
function pickFeatured(list, n) {
    if (list.length <= n) return list;
    const step = Math.floor(list.length / n);
    return Array.from({ length: n }, (_, i) => list[i * step]);
}

/**
 * Build an editorial card HTML string.
 * @param {Object} d - Destination object
 * @param {number} index - Card index (0 = large card)
 * @returns {string}
 */
function buildCard(d, index) {
    const imgSrc = d.image_url || FALLBACK_IMG;
    const region = (d.region || "India").toUpperCase();
    const category = (d.category || "Culture").toUpperCase();
    const budgetLabel = d.budget_level === "low" ? "BUDGET" : d.budget_level === "high" ? "COMFORT" : "MID-RANGE";
    const sizeClass = index === 0 ? "large" : "";
    const desc = d.description || "Discover authentic cultural experiences and hidden local gems.";

    return `
        <article class="editorial-card ${sizeClass}" onclick="window.location.href='destinations.html'" style="cursor:pointer;" aria-label="${escapeAttr(d.name)}">
            <div class="card-img-wrap">
                <img
                    src="${escapeAttr(imgSrc)}"
                    alt="${escapeAttr(d.name)} in ${escapeAttr(d.region || 'India')}"
                    class="card-img"
                    loading="${index === 0 ? 'eager' : 'lazy'}"
                    onerror="this.src='${FALLBACK_IMG}'"
                >
            </div>
            <div class="card-content">
                <div class="card-meta-row">${region} · ${category} · ${budgetLabel}</div>
                <h3 class="card-title">${escapeHtml(d.name)}</h3>
                <p class="card-desc">${escapeHtml(desc)}</p>
            </div>
        </article>
    `;
}

function escapeHtml(text) {
    if (!text) return "";
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}

function escapeAttr(text) {
    if (!text) return "";
    return text.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
