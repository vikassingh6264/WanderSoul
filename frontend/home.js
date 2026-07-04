// WanderSoul — Home Page Logic

function buildFallbackImage(name = "Destination", region = "India") {
    const safeName = String(name || "Destination")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    const safeRegion = String(region || "India")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
            <rect width="1200" height="800" fill="#f8efe1"/>
            <rect x="32" y="32" width="1136" height="736" rx="28" fill="#f4e9d7" stroke="#8d6b2f" stroke-width="4"/>
            <path d="M0 620 C180 540 340 510 520 565 S860 705 1200 610 V800 H0 Z" fill="#d3a65b"/>
            <circle cx="960" cy="220" r="120" fill="#e9c47b" opacity="0.75"/>
            <text x="600" y="330" text-anchor="middle" font-family="Georgia, serif" font-size="42" fill="#4b3420">${safeName}</text>
            <text x="600" y="392" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" fill="#6b4b2f">${safeRegion}</text>
            <text x="600" y="470" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" fill="#6b4b2f">WanderSoul</text>
        </svg>`;
    return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function getImageSrc(destination) {
    const localUrl = destination?.image_url || destination?.image || destination?.photo_url || "";
    if (typeof localUrl === "string" && localUrl.trim()) {
        return localUrl;
    }
    return buildFallbackImage(destination?.name, destination?.region || destination?.state);
}

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
            heroImg.src = getImageSrc(destinations[0]);
            heroImg.alt = `${destinations[0].name} — ${destinations[0].region}`;
            heroImg.onerror = () => {
                heroImg.src = buildFallbackImage(destinations[0]?.name, destinations[0]?.region || destinations[0]?.state);
            };
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
        if (heroImg && !heroImg.src) heroImg.src = buildFallbackImage();
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
    const imgSrc = getImageSrc(d);
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
                    onerror="this.src='${buildFallbackImage(d.name, d.region || d.state)}'"
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
