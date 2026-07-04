/**
 * WanderSoul — Frontend Application Logic
 *
 * Handles form submission, API calls, result rendering,
 * tab navigation, loading states, and error handling.
 * No framework dependencies — pure vanilla JS.
 */

// ─── DOM Elements ───────────────────────────────────────────────

const form = document.getElementById("discovery-form");
const submitBtn = document.getElementById("submit-btn");
const resultsSection = document.getElementById("results-section");
const resultsSummary = document.getElementById("results-summary");
const errorState = document.getElementById("error-state");
const errorMessage = document.getElementById("error-message");
const retryBtn = document.getElementById("retry-btn");

// Tab elements
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");

// API base URL — same origin in production
const API_BASE = window.location.origin;

// ─── Form Submission ────────────────────────────────────────────

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await handleDiscovery();
});

retryBtn.addEventListener("click", () => {
    errorState.classList.add("hidden");
    form.scrollIntoView({ behavior: "smooth" });
});

/**
 * Collect form data, call the API, and render results.
 */
async function handleDiscovery() {
    const formData = collectFormData();

    if (!validateForm(formData)) {
        return;
    }

    showLoading();
    hideError();
    hideResults();

    try {
        const response = await fetch(`${API_BASE}/api/discover`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Request failed (${response.status})`);
        }

        const data = await response.json();
        renderResults(data);
    } catch (error) {
        showError(error.message || "Something went wrong. Please try again.");
    } finally {
        hideLoading();
    }
}

/**
 * Collect form data into the API request format.
 * @returns {Object} TravelRequest-shaped object
 */
function collectFormData() {
    const query = document.getElementById("query-input").value.trim();
    const budget = document.getElementById("budget-select").value;
    const days = parseInt(document.getElementById("days-input").value, 10);
    const accessibility = document.getElementById("accessibility-select").value;

    const interests = [];
    document.querySelectorAll('input[name="interests"]:checked').forEach((cb) => {
        interests.push(cb.value);
    });

    return { query, budget, days, interests, accessibility };
}

/**
 * Client-side validation before API call.
 * @param {Object} data - The form data object
 * @returns {boolean} True if valid
 */
function validateForm(data) {
    if (!data.query || data.query.length < 3) {
        showError("Please describe what you're looking for (at least 3 characters).");
        return false;
    }
    if (!data.days || data.days < 1 || data.days > 30) {
        showError("Days must be between 1 and 30.");
        return false;
    }
    return true;
}

// ─── Loading State ──────────────────────────────────────────────

function showLoading() {
    submitBtn.classList.add("loading");
    submitBtn.disabled = true;

    // Show skeleton loading in results area
    resultsSection.classList.remove("hidden");
    resultsSummary.textContent = "Discovering your perfect cultural journey...";

    // Reset tabs to first
    activateTab("tab-destinations");

    const panel = document.getElementById("panel-destinations");
    panel.innerHTML = createSkeletonCards(3);
}

function hideLoading() {
    submitBtn.classList.remove("loading");
    submitBtn.disabled = false;
}

/**
 * Generate skeleton loading cards HTML.
 * @param {number} count - Number of skeleton cards
 * @returns {string} HTML string
 */
function createSkeletonCards(count) {
    let html = "";
    for (let i = 0; i < count; i++) {
        html += `
            <div class="skeleton-card" aria-hidden="true">
                <div class="skeleton-line skeleton-line-title"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line skeleton-line-short"></div>
            </div>
        `;
    }
    return html;
}

// ─── Error Handling ─────────────────────────────────────────────

function showError(message) {
    errorMessage.textContent = message;
    errorState.classList.remove("hidden");
    hideResults();
    errorState.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideError() {
    errorState.classList.add("hidden");
}

// ─── Results Rendering ──────────────────────────────────────────

function hideResults() {
    resultsSection.classList.add("hidden");
}

/**
 * Render the full API response into tab panels.
 * @param {Object} data - TravelResponse from the API
 */
function renderResults(data) {
    resultsSection.classList.remove("hidden");
    resultsSummary.textContent = data.summary || "Here's what we found for you!";

    // Render each panel
    renderDestinations(data.destinations || []);
    renderHiddenGems(data.hidden_gems || []);
    renderHeritage(data.heritage || []);
    renderEvents(data.events || []);
    renderExperiences(data.experiences || []);
    renderStory(data.story);

    // Auto-select best tab (first one with results)
    const firstTabWithResults = findFirstTabWithResults(data);
    activateTab(firstTabWithResults);

    // Update tab badges
    updateTabBadges(data);

    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/**
 * Find the first tab that has results to display.
 * @param {Object} data - API response
 * @returns {string} Tab button ID
 */
function findFirstTabWithResults(data) {
    if (data.destinations?.length) return "tab-destinations";
    if (data.hidden_gems?.length) return "tab-gems";
    if (data.heritage?.length) return "tab-heritage";
    if (data.events?.length) return "tab-events";
    if (data.experiences?.length) return "tab-experiences";
    if (data.story) return "tab-story";
    return "tab-destinations";
}

/**
 * Update tab button text with result counts.
 * @param {Object} data - API response
 */
function updateTabBadges(data) {
    const counts = {
        "tab-destinations": data.destinations?.length || 0,
        "tab-gems": data.hidden_gems?.length || 0,
        "tab-heritage": data.heritage?.length || 0,
        "tab-events": data.events?.length || 0,
        "tab-experiences": data.experiences?.length || 0,
        "tab-story": data.story ? 1 : 0,
    };

    for (const [tabId, count] of Object.entries(counts)) {
        const btn = document.getElementById(tabId);
        if (btn && count === 0) {
            btn.style.opacity = "0.4";
        } else if (btn) {
            btn.style.opacity = "1";
        }
    }
}

// ─── Panel Renderers ────────────────────────────────────────────

function renderDestinations(destinations) {
    const panel = document.getElementById("panel-destinations");
    if (!destinations.length) {
        panel.innerHTML = createEmptyState("🏛️", "No destination matches found. Try broadening your interests.");
        return;
    }
    panel.innerHTML = destinations.map((d) => `
        <article class="result-card">
            <div class="result-card-header">
                <div>
                    <h3 class="result-card-title">${escapeHtml(d.name)}</h3>
                    <p class="result-card-subtitle">${escapeHtml(d.region)}</p>
                </div>
                ${d.budget_tip ? `<span class="result-card-badge">${escapeHtml(d.budget_tip)}</span>` : ""}
            </div>
            <div class="result-card-body">
                <p>${escapeHtml(d.match_reason)}</p>
            </div>
            ${d.highlights?.length ? `
                <div class="result-card-meta">
                    ${d.highlights.map((h) => `<span class="meta-tag">${escapeHtml(h)}</span>`).join("")}
                </div>
            ` : ""}
        </article>
    `).join("");
}

function renderHiddenGems(gems) {
    const panel = document.getElementById("panel-gems");
    if (!gems.length) {
        panel.innerHTML = createEmptyState("💎", "No hidden gems found for your criteria. Adjust your interests to discover more.");
        return;
    }
    panel.innerHTML = gems.map((g) => `
        <article class="result-card">
            <div class="result-card-header">
                <div>
                    <h3 class="result-card-title">${escapeHtml(g.name)}</h3>
                    <p class="result-card-subtitle">${escapeHtml(g.location)}</p>
                </div>
            </div>
            <div class="result-card-body">
                <p>${escapeHtml(g.description)}</p>
            </div>
            ${g.why_hidden ? `
                <div class="result-card-tip">
                    <strong>Why most tourists miss this:</strong> ${escapeHtml(g.why_hidden)}
                </div>
            ` : ""}
            ${g.local_tip ? `
                <div class="result-card-tip">
                    <strong>Local tip:</strong> ${escapeHtml(g.local_tip)}
                </div>
            ` : ""}
        </article>
    `).join("");
}

function renderHeritage(heritage) {
    const panel = document.getElementById("panel-heritage");
    if (!heritage.length) {
        panel.innerHTML = createEmptyState("🏰", "No heritage sites matched. Try adding 'heritage' to your interests.");
        return;
    }
    panel.innerHTML = heritage.map((h) => `
        <article class="result-card">
            <div class="result-card-header">
                <div>
                    <h3 class="result-card-title">${escapeHtml(h.name)}</h3>
                </div>
            </div>
            <div class="result-card-body">
                <p>${escapeHtml(h.significance)}</p>
            </div>
            ${h.how_to_engage ? `
                <div class="result-card-tip">
                    <strong>How to engage:</strong> ${escapeHtml(h.how_to_engage)}
                </div>
            ` : ""}
            ${h.preservation_note ? `
                <div class="result-card-tip">
                    <strong>Preservation:</strong> ${escapeHtml(h.preservation_note)}
                </div>
            ` : ""}
        </article>
    `).join("");
}

function renderEvents(events) {
    const panel = document.getElementById("panel-events");
    if (!events.length) {
        panel.innerHTML = createEmptyState("🎪", "No events found. Try different interests or check back closer to your travel dates.");
        return;
    }
    panel.innerHTML = events.map((e) => `
        <article class="result-card">
            <div class="result-card-header">
                <div>
                    <h3 class="result-card-title">${escapeHtml(e.name)}</h3>
                    <p class="result-card-subtitle">${escapeHtml(e.location)}</p>
                </div>
                <span class="result-card-badge">${escapeHtml(e.timing)}</span>
            </div>
            <div class="result-card-body">
                <p>${escapeHtml(e.description)}</p>
            </div>
            ${e.traveler_relevance ? `
                <div class="result-card-tip">
                    <strong>Why this fits you:</strong> ${escapeHtml(e.traveler_relevance)}
                </div>
            ` : ""}
        </article>
    `).join("");
}

function renderExperiences(experiences) {
    const panel = document.getElementById("panel-experiences");
    if (!experiences.length) {
        panel.innerHTML = createEmptyState("🤝", "No experiences matched. Try broadening your interests for more options.");
        return;
    }
    panel.innerHTML = experiences.map((e) => `
        <article class="result-card">
            <div class="result-card-header">
                <div>
                    <h3 class="result-card-title">${escapeHtml(e.name)}</h3>
                    <p class="result-card-subtitle">${escapeHtml(e.type)}</p>
                </div>
                ${e.budget_estimate ? `<span class="result-card-badge">${escapeHtml(e.budget_estimate)}</span>` : ""}
            </div>
            <div class="result-card-body">
                <p>${escapeHtml(e.description)}</p>
            </div>
            ${e.booking_tip ? `
                <div class="result-card-tip">
                    <strong>Booking tip:</strong> ${escapeHtml(e.booking_tip)}
                </div>
            ` : ""}
        </article>
    `).join("");
}

function renderStory(story) {
    const panel = document.getElementById("panel-story");
    if (!story) {
        panel.innerHTML = createEmptyState("📖", "No story generated for this query. Try asking to 'explore' or 'plan a trip' for immersive storytelling.");
        return;
    }

    const paragraphs = story.narrative
        .split("\n")
        .filter((p) => p.trim())
        .map((p) => `<p>${escapeHtml(p)}</p>`)
        .join("");

    panel.innerHTML = `
        <div class="story-destination">${escapeHtml(story.destination)}</div>
        <div class="story-narrative">${paragraphs}</div>
        ${story.themes?.length ? `
            <div class="story-themes">
                ${story.themes.map((t) => `<span class="meta-tag">${escapeHtml(t)}</span>`).join("")}
            </div>
        ` : ""}
    `;
}

// ─── Tab Navigation ─────────────────────────────────────────────

tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
        activateTab(btn.id);
    });

    // Keyboard navigation: arrow keys between tabs
    btn.addEventListener("keydown", (event) => {
        const tabs = Array.from(tabButtons);
        const currentIndex = tabs.indexOf(btn);

        let targetIndex = -1;
        if (event.key === "ArrowRight" || event.key === "ArrowDown") {
            targetIndex = (currentIndex + 1) % tabs.length;
        } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
            targetIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        }

        if (targetIndex >= 0) {
            event.preventDefault();
            tabs[targetIndex].focus();
            activateTab(tabs[targetIndex].id);
        }
    });
});

/**
 * Activate a tab and show its panel.
 * @param {string} tabId - The tab button's ID
 */
function activateTab(tabId) {
    // Deactivate all tabs
    tabButtons.forEach((btn) => {
        btn.classList.remove("active");
        btn.setAttribute("aria-selected", "false");
        btn.setAttribute("tabindex", "-1");
    });

    // Hide all panels
    tabPanels.forEach((panel) => {
        panel.classList.add("hidden");
        panel.classList.remove("active");
    });

    // Activate selected tab
    const activeTab = document.getElementById(tabId);
    if (activeTab) {
        activeTab.classList.add("active");
        activeTab.setAttribute("aria-selected", "true");
        activeTab.setAttribute("tabindex", "0");

        const panelId = activeTab.getAttribute("aria-controls");
        const activePanel = document.getElementById(panelId);
        if (activePanel) {
            activePanel.classList.remove("hidden");
            activePanel.classList.add("active");
        }
    }
}

// ─── Utility Functions ──────────────────────────────────────────

/**
 * Escape HTML to prevent XSS.
 * @param {string} text - Raw text
 * @returns {string} HTML-safe text
 */
function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Create an empty state HTML block.
 * @param {string} icon - Emoji icon
 * @param {string} message - Help text
 * @returns {string} HTML string
 */
function createEmptyState(icon, message) {
    return `
        <div class="empty-state">
            <div class="empty-state-icon">${icon}</div>
            <p class="empty-state-text">${escapeHtml(message)}</p>
        </div>
    `;
}
