// WanderSoul — Destination Detail Page Logic

const STATE_CODES = {
    "Karnataka": "KA", "Uttar Pradesh": "UP", "Rajasthan": "RJ", "Kerala": "KL",
    "Meghalaya": "ML", "Gujarat": "GJ", "Madhya Pradesh": "MP", "Andhra Pradesh": "AP",
    "Arunachal Pradesh": "AR", "Assam": "AS", "Bihar": "BR", "Chhattisgarh": "CG",
    "Goa": "GA", "Haryana": "HR", "Himachal Pradesh": "HP", "Jharkhand": "JH",
    "Maharashtra": "MH", "Punjab": "PB", "Odisha": "OR", "Tamil Nadu": "TN",
    "Sikkim": "SK", "Manipur": "MN", "Mizoram": "MZ", "Nagaland": "NL",
    "Tripura": "TR", "Telangana": "TG", "Uttarakhand": "UK", "West Bengal": "WB"
};

function getBestSeason(state) {
    const s = state.toLowerCase();
    if (s.includes("rajasthan") || s.includes("gujarat") || s.includes("uttar pradesh") || s.includes("delhi") || s.includes("punjab") || s.includes("haryana")) {
        return "OCT TO MAR (WINTER)";
    }
    if (s.includes("kerala") || s.includes("karnataka") || s.includes("tamil nadu") || s.includes("andhra pradesh") || s.includes("telangana") || s.includes("goa")) {
        return "NOV TO FEB (DRY)";
    }
    if (s.includes("meghalaya") || s.includes("arunachal") || s.includes("sikkim") || s.includes("manipur") || s.includes("mizoram") || s.includes("nagaland") || s.includes("tripura") || s.includes("assam")) {
        return "MAR TO JUN (SPRING)";
    }
    if (s.includes("himachal") || s.includes("uttarakhand") || s.includes("kashmir")) {
        return "APR TO JUN (SUMMER)";
    }
    return "OCT TO MAR (COOL)";
}

function getNearestAirport(state) {
    const s = state.toLowerCase();
    if (s.includes("rajasthan")) return "JAIPUR (JAI)";
    if (s.includes("karnataka")) return "BENGALURU (BLR)";
    if (s.includes("kerala")) return "KOCHI (COK)";
    if (s.includes("tamil nadu")) return "CHENNAI (MAA)";
    if (s.includes("maharashtra")) return "MUMBAI (BOM)";
    if (s.includes("delhi") || s.includes("haryana")) return "DELHI (DEL)";
    if (s.includes("uttar pradesh")) return "VARANASI (VNS)";
    if (s.includes("west bengal")) return "BAGDOGRA (IXB)";
    if (s.includes("meghalaya") || s.includes("assam")) return "GUWAHATI (GAU)";
    if (s.includes("goa")) return "GOA INTL (GOI)";
    if (s.includes("gujarat")) return "AHMEDABAD (AMD)";
    if (s.includes("sikkim")) return "BAGDOGRA (IXB)";
    if (s.includes("madhya pradesh")) return "INDORE (IDR)";
    if (s.includes("odisha")) return "BHUBANESWAR (BBI)";
    return "LOCAL STATE HUB";
}

document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    const destId = params.get("id");

    if (!destId) {
        showError("Invalid parameter: ID missing.");
        return;
    }

    await loadDestinationDetail(destId);
});

function showError(message) {
    document.getElementById("detail-loading").classList.add("hidden");
    document.getElementById("detail-error").classList.remove("hidden");
    document.getElementById("error-text").textContent = message;
}

async function loadDestinationDetail(destId) {
    try {
        const response = await fetch("/api/destinations");
        if (!response.ok) throw new Error("Could not connect to destinations database.");
        
        const data = await response.json();
        const dest = (data.destinations || []).find(d => d.id === destId);

        if (!dest) {
            showError(`Destination with ID '${destId}' could not be located in our journals.`);
            return;
        }

        renderDetail(dest);
    } catch (err) {
        console.error(err);
        showError(err.message || "Failed to load log entries.");
    }
}

function renderDetail(d) {
    document.getElementById("detail-loading").classList.add("hidden");
    document.getElementById("detail-content").classList.remove("hidden");

    // Main elements
    const stateCode = STATE_CODES[d.region] || "IND";
    document.getElementById("detail-img").src = d.image_url || "https://upload.wikimedia.org/wikipedia/commons/c/cb/Hampi_virupaksha_temple.jpg";
    document.getElementById("detail-img").alt = `${d.name} in ${d.region}`;
    document.getElementById("detail-badge-text").textContent = `${stateCode}-DET`;
    document.getElementById("detail-category").textContent = d.category;
    document.getElementById("detail-title").textContent = d.name;
    document.getElementById("detail-desc").textContent = d.description || "No journal notes recorded yet.";

    // Fact strip
    document.getElementById("fact-season").textContent = getBestSeason(d.region);
    const budgetLabel = d.budget_level === "low" ? "₹1K-3K/DAY" : (d.budget_level === "medium" ? "₹5K-10K/DAY" : "₹15K+/DAY");
    document.getElementById("fact-budget").textContent = budgetLabel;
    document.getElementById("fact-airport").textContent = getNearestAirport(d.region);

    // Highlights list
    const highlightsList = document.getElementById("detail-highlights-list");
    highlightsList.innerHTML = "";

    const items = [];
    if (d.heritage_sites && d.heritage_sites.length > 0) {
        items.push(`<li><strong>HERITAGE</strong> <strong>${d.heritage_sites[0].name}</strong>: ${d.heritage_sites[0].significance}</li>`);
    }
    if (d.hidden_gems && d.hidden_gems.length > 0) {
        d.hidden_gems.slice(0, 2).forEach(gem => {
            items.push(`<li><strong>HIDDEN GEM</strong> <strong>${gem.name}</strong>: ${gem.description}</li>`);
        });
    }
    if (d.cultural_experiences && d.cultural_experiences.length > 0) {
        items.push(`<li><strong>EXPERIENCE</strong> <strong>${d.cultural_experiences[0].name}</strong>: ${d.cultural_experiences[0].description}</li>`);
    }
    if (d.local_events && d.local_events.length > 0) {
        items.push(`<li><strong>LOCAL EVENT</strong> <strong>${d.local_events[0].name}</strong> (${d.local_events[0].timing}): ${d.local_events[0].description}</li>`);
    }

    if (items.length === 0) {
        highlightsList.innerHTML = "<li>No specific highlights recorded yet for this coordinates.</li>";
    } else {
        highlightsList.innerHTML = items.join("");
    }

    // Gallery (loose polaroids)
    const galleryScroll = document.getElementById("gallery-scroll");
    galleryScroll.innerHTML = "";

    const galleryPhotos = [
        { title: "Main Sight", url: d.image_url },
        ...(d.hidden_gems || []).map(g => ({ title: g.name, url: d.image_url })), // Reusing image with different captions since we have single main URL
        ...(d.cultural_experiences || []).map(e => ({ title: e.name, url: d.image_url })),
        ...(d.heritage_sites || []).map(h => ({ title: h.name, url: d.image_url }))
    ].slice(0, 4); // Limit to top 4 cards

    const rotations = ["-1.5deg", "2deg", "-2.5deg", "1.5deg"];

    galleryScroll.innerHTML = galleryPhotos.map((photo, index) => {
        const rot = rotations[index % rotations.length];
        return `
            <div class="gallery-card" style="--rot: ${rot};">
                <img src="${photo.url || 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Hampi_virupaksha_temple.jpg'}" alt="${photo.title}" class="gallery-img" loading="lazy">
                <div class="gallery-title">${photo.title}</div>
            </div>
        `;
    }).join("");

    // Ticket CTA
    document.getElementById("ticket-code").textContent = `TICKET REF: WS-IND-${stateCode.toUpperCase()}-${d.id.substring(0,3).toUpperCase()}`;
    document.getElementById("plan-trip-link").href = `plan.html?destination=${d.id}`;
}
