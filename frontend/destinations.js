// WanderSoul — Destinations Listing Logic

const STATE_TO_REGION = {
    "Uttar Pradesh": "North",
    "Punjab": "North",
    "Haryana": "North",
    "Himachal Pradesh": "North",
    "Uttarakhand": "North",
    "Karnataka": "South",
    "Kerala": "South",
    "Andhra Pradesh": "South",
    "Tamil Nadu": "South",
    "Telangana": "South",
    "Bihar": "East",
    "Jharkhand": "East",
    "Odisha": "East",
    "West Bengal": "East",
    "Rajasthan": "West",
    "Gujarat": "West",
    "Goa": "West",
    "Maharashtra": "West",
    "Meghalaya": "Northeast",
    "Arunachal Pradesh": "Northeast",
    "Assam": "Northeast",
    "Sikkim": "Northeast",
    "Manipur": "Northeast",
    "Mizoram": "Northeast",
    "Nagaland": "Northeast",
    "Tripura": "Northeast",
    "Madhya Pradesh": "Central",
    "Chhattisgarh": "Central"
};

const STATE_CODES = {
    "Karnataka": "KA", "Uttar Pradesh": "UP", "Rajasthan": "RJ", "Kerala": "KL",
    "Meghalaya": "ML", "Gujarat": "GJ", "Madhya Pradesh": "MP", "Andhra Pradesh": "AP",
    "Arunachal Pradesh": "AR", "Assam": "AS", "Bihar": "BR", "Chhattisgarh": "CG",
    "Goa": "GA", "Haryana": "HR", "Himachal Pradesh": "HP", "Jharkhand": "JH",
    "Maharashtra": "MH", "Punjab": "PB", "Odisha": "OR", "Tamil Nadu": "TN",
    "Sikkim": "SK", "Manipur": "MN", "Mizoram": "MZ", "Nagaland": "NL",
    "Tripura": "TR", "Telangana": "TG", "Uttarakhand": "UK", "West Bengal": "WB"
};

let allDestinations = [];
let activeSort = "name";

// DOM Elements
const destinationsGrid = document.getElementById("destinations-grid");
const resultsCount = document.getElementById("results-count");
const sortNameBtn = document.getElementById("sort-name");
const sortRegionBtn = document.getElementById("sort-region");

// Initialize page
document.addEventListener("DOMContentLoaded", async () => {
    await fetchDestinations();
    setupFilters();
    setupSort();
});

async function fetchDestinations() {
    try {
        const response = await fetch("/api/destinations");
        if (!response.ok) throw new Error("Failed to fetch destinations");
        const data = await response.json();
        allDestinations = data.destinations || [];
        filterAndRender();
    } catch (err) {
        console.error(err);
        destinationsGrid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-title">System Error</div>
                <p>Could not retrieve the destinations log. Please refresh the page.</p>
            </div>
        `;
        resultsCount.textContent = "Error loading logs";
    }
}

function setupFilters() {
    const checkboxes = document.querySelectorAll(".stamp-checkbox");
    checkboxes.forEach(cb => {
        cb.addEventListener("change", () => {
            filterAndRender();
        });
    });
}

function setupSort() {
    sortNameBtn.addEventListener("click", () => {
        sortNameBtn.classList.add("active");
        sortRegionBtn.classList.remove("active");
        activeSort = "name";
        filterAndRender();
    });

    sortRegionBtn.addEventListener("click", () => {
        sortRegionBtn.classList.add("active");
        sortNameBtn.classList.remove("active");
        activeSort = "region";
        filterAndRender();
    });
}

function getActiveFilters() {
    const regions = [];
    const budgets = [];
    const dayRanges = [];
    const interests = [];

    document.querySelectorAll(".stamp-checkbox:checked").forEach(cb => {
        const id = cb.id;
        if (id.startsWith("region-")) {
            regions.push(cb.value);
        } else if (id.startsWith("budget-")) {
            budgets.push(cb.value);
        } else if (id.startsWith("days-")) {
            dayRanges.push(cb.value);
        } else if (id.startsWith("int-")) {
            interests.push(cb.value);
        }
    });

    return { regions, budgets, dayRanges, interests };
}

function filterAndRender() {
    const filters = getActiveFilters();
    
    let filtered = allDestinations.filter(d => {
        // 1. Region Filter
        const destRegion = STATE_TO_REGION[d.region] || "Central";
        if (filters.regions.length > 0 && !filters.regions.includes(destRegion)) {
            return false;
        }

        // 2. Budget Filter
        if (filters.budgets.length > 0 && !filters.budgets.includes(d.budget_level)) {
            return false;
        }

        // 3. Duration Filter
        if (filters.dayRanges.length > 0) {
            const hasMatch = filters.dayRanges.some(range => {
                if (range === "short") {
                    return d.best_for_days.some(day => day <= 2);
                } else if (range === "medium") {
                    return d.best_for_days.some(day => day === 3 || day === 4);
                } else if (range === "long") {
                    return d.best_for_days.some(day => day >= 5);
                }
                return false;
            });
            if (!hasMatch) return false;
        }

        // 4. Interests Filter
        if (filters.interests.length > 0) {
            const hasInterest = filters.interests.some(interest => d.tags.includes(interest));
            if (!hasInterest) return false;
        }

        return true;
    });

    // Sort results
    if (activeSort === "name") {
        filtered.sort((a, b) => a.name.localeCompare(b.name));
    } else {
        filtered.sort((a, b) => {
            const rA = STATE_TO_REGION[a.region] || "Central";
            const rB = STATE_TO_REGION[b.region] || "Central";
            return rA.localeCompare(rB);
        });
    }

    renderDestinations(filtered);
}

function escapeHtml(text) {
    if (!text) return "";
    const el = document.createElement("div");
    el.textContent = String(text);
    return el.innerHTML;
}

function escapeAttr(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

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
            <rect width="1200" height="800" fill="#f7efe0"/>
            <rect x="32" y="32" width="1136" height="736" rx="28" fill="#f0dfc0" stroke="#8f6b2f" stroke-width="4"/>
            <path d="M0 640 C220 560 360 525 540 570 S890 710 1200 610 V800 H0 Z" fill="#d8a85a"/>
            <circle cx="970" cy="225" r="120" fill="#e7c576" opacity="0.75"/>
            <text x="600" y="330" text-anchor="middle" font-family="Georgia, serif" font-size="42" fill="#4a321d">${safeName}</text>
            <text x="600" y="392" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" fill="#6d4e2d">${safeRegion}</text>
            <text x="600" y="470" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" fill="#6d4e2d">WanderSoul</text>
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

function renderDestinations(list) {
    resultsCount.textContent = `${list.length} entries found`;

    if (list.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.style.gridColumn = "1 / -1";
        empty.innerHTML = `<div class="empty-state-title">No Stamps Match</div><p>Try clearing some filters to expand your journal search.</p>`;
        destinationsGrid.innerHTML = "";
        destinationsGrid.appendChild(empty);
        return;
    }

    destinationsGrid.innerHTML = "";
    list.forEach((d, index) => {
        const region     = d.region   || "India";
        const category   = d.category || "General";
        const stateCode  = STATE_CODES[region] || "IND";
        const budgetLabel = d.budget_level === "low" ? "BUDGET" : (d.budget_level === "medium" ? "MID-RANGE" : "COMFORT");
        const hasDays    = Array.isArray(d.best_for_days) && d.best_for_days.length > 0;
        const daysLabel  = hasDays ? `${Math.min(...d.best_for_days)}\u2013${Math.max(...d.best_for_days)}D` : "1-30D";
        const imgSrc     = getImageSrc(d);

        const card = document.createElement("article");
        card.className = "editorial-card";
        card.setAttribute("aria-labelledby", `title-${escapeAttr(d.id)}`);
        card.style.cursor = "pointer";
        card.addEventListener("click", () => {
            window.location.href = `detail.html?id=${encodeURIComponent(d.id)}`;
        });
        card.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                window.location.href = `detail.html?id=${encodeURIComponent(d.id)}`;
            }
        });
        card.setAttribute("tabindex", "0");
        card.setAttribute("role", "button");

        const wrap = document.createElement("div");
        wrap.className = "card-img-wrap";

        const img = document.createElement("img");
        img.src = imgSrc;
        img.alt = `${d.name} in ${region}`;
        img.className = "card-img";
        img.loading = "lazy";
        img.onerror = () => { img.src = buildFallbackImage(d.name, d.region || d.state); };

        const badge = document.createElement("div");
        badge.className = "stamp-badge";
        badge.setAttribute("aria-hidden", "true");
        badge.innerHTML = `<span class="stamp-text">${escapeHtml(stateCode)}-${String(index + 1).padStart(2, "0")}</span>`;

        wrap.appendChild(img);
        wrap.appendChild(badge);

        const content = document.createElement("div");
        content.className = "card-content";

        const meta = document.createElement("div");
        meta.className = "card-meta-row";
        meta.textContent = `${region.toUpperCase()} \u00b7 ${category.toUpperCase()} \u00b7 ${budgetLabel} \u00b7 ${daysLabel}`;

        const title = document.createElement("h3");
        title.id = `title-${escapeAttr(d.id)}`;
        title.className = "card-title";
        title.textContent = d.name;

        const desc = document.createElement("p");
        desc.className = "card-desc";
        desc.textContent = d.description || "Discover historic architecture, regional art forms, and rich heritage experiences.";

        content.appendChild(meta);
        content.appendChild(title);
        content.appendChild(desc);
        card.appendChild(wrap);
        card.appendChild(content);
        destinationsGrid.appendChild(card);
    });
}

