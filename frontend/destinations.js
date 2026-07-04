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

function renderDestinations(list) {
    resultsCount.textContent = `${list.length} entries found`;

    if (list.length === 0) {
        destinationsGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-state-title">No Stamps Match</div>
                <p>Try clearing some filters to expand your journal search.</p>
            </div>
        `;
        return;
    }

    destinationsGrid.innerHTML = list.map((d, index) => {
        const region    = d.region   || "India";
        const category  = d.category || "General";
        const stateCode = STATE_CODES[region] || "IND";
        const budgetLabel = d.budget_level === "low" ? "BUDGET" : (d.budget_level === "medium" ? "MID-RANGE" : "COMFORT");
        const days = Array.isArray(d.best_for_days) && d.best_for_days.length > 0;
        const daysLabel = days ? `${Math.min(...d.best_for_days)}\u2013${Math.max(...d.best_for_days)}D` : "1-30D";
        
        return `
            <article class="editorial-card" onclick="window.location.href='detail.html?id=${d.id}'" aria-labelledby="title-${d.id}">
                <div class="card-img-wrap">
                    <img 
                        src="${d.image_url || 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Hampi_virupaksha_temple.jpg'}" 
                        alt="${d.name} in ${region}" 
                        class="card-img"
                        loading="lazy"
                    >
                    <div class="stamp-badge" aria-hidden="true">
                        <span class="stamp-text">${stateCode}-${(index + 1).toString().padStart(2, '0')}</span>
                    </div>
                </div>
                <div class="card-content">
                    <div class="card-meta-row">${region.toUpperCase()} · ${category.toUpperCase()} · ${budgetLabel} · ${daysLabel}</div>
                    <h3 id="title-${d.id}" class="card-title">${d.name}</h3>
                    <p class="card-desc">${d.description || 'Discover historic architecture, regional art forms, and rich heritage experiences.'}</p>
                </div>
            </article>
        `;
    }).join("");
}

