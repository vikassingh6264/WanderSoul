// WanderSoul — Itinerary Planner Javascript Logic

document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    const prefillDestId = params.get("destination");

    if (prefillDestId) {
        await prefillForm(prefillDestId);
    }

    setupFormSubmission();
});

async function prefillForm(destId) {
    try {
        const response = await fetch("/api/destinations");
        if (!response.ok) return;
        const data = await response.json();
        const dest = (data.destinations || []).find(d => d.id === destId);
        
        if (dest) {
            // Fill query
            const queryArea = document.getElementById("query-input");
            queryArea.value = `I want to explore the history, cultural spots, and local food in ${dest.name}, ${dest.region}.`;
            
            // Set days
            const daysInput = document.getElementById("days-input");
            if (dest.best_for_days && dest.best_for_days.length > 0) {
                // Find median or average
                const mid = Math.round(dest.best_for_days.length / 2);
                daysInput.value = dest.best_for_days[mid - 1] || 3;
            } else {
                daysInput.value = 3;
            }

            // Set budget
            const budgetSelect = document.getElementById("budget-select");
            budgetSelect.value = dest.budget_level || "medium";

            // Check matching interests
            document.querySelectorAll(".stamp-checkbox[name='interests']").forEach(cb => {
                if (dest.tags.includes(cb.value)) {
                    cb.checked = true;
                } else {
                    cb.checked = false; // reset default
                }
            });
        }
    } catch (err) {
        console.error("Failed to prefill form:", err);
    }
}

function setupFormSubmission() {
    const form = document.getElementById("itinerary-form");
    const submitBtn = document.getElementById("submit-btn");
    const loadingState = document.getElementById("itinerary-loading");
    const loadingTitle = document.getElementById("loading-title");
    const loadingDesc = document.getElementById("loading-desc");
    const errorState = document.getElementById("itinerary-error");
    const errorMessage = document.getElementById("error-message");
    const resultsState = document.getElementById("itinerary-results");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // 1. Gather fields
        const query = document.getElementById("query-input").value.trim();
        const days = parseInt(document.getElementById("days-input").value, 10);
        const budget = document.getElementById("budget-select").value;
        const accessibility = document.getElementById("accessibility-select").value;

        const interests = [];
        document.querySelectorAll(".stamp-checkbox[name='interests']:checked").forEach(cb => {
            interests.push(cb.value);
        });

        // 2. Validate
        if (!query || query.length < 3) {
            errorMessage.textContent = "Please input a search query (minimum 3 characters).";
            errorState.classList.remove("hidden");
            return;
        }
        if (isNaN(days) || days < 1 || days > 30) {
            errorMessage.textContent = "Voyage duration must be between 1 and 30 days.";
            errorState.classList.remove("hidden");
            return;
        }

        // 3. Show Loading
        loadingTitle.textContent = `Routing your ${days}-day itinerary...`;
        loadingDesc.textContent = `Registering tickets and querying regional archives for cultural highlights.`;
        loadingState.classList.remove("hidden");
        loadingState.setAttribute("aria-busy", "true");
        form.setAttribute("aria-busy", "true");
        errorState.classList.add("hidden");
        resultsState.classList.add("hidden");
        submitBtn.disabled = true;
        submitBtn.setAttribute("aria-disabled", "true");

        // Scroll to loading area
        loadingState.scrollIntoView({ behavior: "smooth", block: "center" });

        try {
            const response = await fetch("/api/discover", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query, budget, days, interests, accessibility })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Server returned error status (${response.status})`);
            }

            const data = await response.json();
            renderItinerary(data, days);
        } catch (err) {
            console.error(err);
            errorMessage.textContent = err.message || "Failed to generate itinerary. The routing engine may be temporarily offline.";
            errorState.classList.remove("hidden");
        } finally {
            loadingState.classList.add("hidden");
            loadingState.setAttribute("aria-busy", "false");
            form.setAttribute("aria-busy", "false");
            submitBtn.disabled = false;
            submitBtn.setAttribute("aria-disabled", "false");
        }
    });
}

function renderItinerary(data, daysCount) {
    const resultsState = document.getElementById("itinerary-results");
    const summaryText = document.getElementById("itinerary-summary");
    const timelineFlow = document.getElementById("timeline-flow");
    const storySegment = document.getElementById("story-segment");
    const storyText = document.getElementById("story-text");

    // Show results
    resultsState.classList.remove("hidden");
    summaryText.textContent = data.summary || "Custom route log compiled successfully.";

    // Render timeline
    timelineFlow.innerHTML = "";

    // Day titles list
    const dayThemes = [
        { title: "Arrival & Orientation", desc: "Arrive at the destination and check in. Immerse yourself in the surrounding architecture and local markets." },
        { title: "Heritage Exploration", desc: "Dive deep into the historical significance and monumental architecture of the region." },
        { title: "Local Connections & Crafts", desc: "Interact with local artisans and workshops to learn traditional methods of production." },
        { title: "Nature & Hidden Wonders", desc: "Step off the beaten path to explore waterfalls, scenic trails, and remote viewpoints." },
        { title: "Local Cuisine & Festivities", desc: "Explore local food stalls, heritage eateries, and experience cultural performances or festivals." },
        { title: "Departure & Reflection", desc: "Take a quiet morning walk, pack your journal, and proceed to the transit hub for departure." }
    ];

    // Distribute data across days
    const timelineDays = [];
    for (let i = 0; i < daysCount; i++) {
        const theme = dayThemes[i % dayThemes.length];
        timelineDays.push({
            dayNum: i + 1,
            title: theme.title,
            desc: theme.desc,
            destinations: [],
            heritage: [],
            gems: [],
            experiences: [],
            events: []
        });
    }

    // Distribute logic
    // 1. Destinations on Day 1
    if (data.destinations && data.destinations.length > 0) {
        timelineDays[0].destinations.push(...data.destinations);
    }

    // 2. Heritage Sites on Day 1 & Day 2
    if (data.heritage && data.heritage.length > 0) {
        data.heritage.forEach((site, index) => {
            const targetDay = index % Math.min(daysCount, 2);
            timelineDays[targetDay].heritage.push(site);
        });
    }

    // 3. Hidden Gems on intermediate days
    if (data.hidden_gems && data.hidden_gems.length > 0) {
        data.hidden_gems.forEach((gem, index) => {
            const targetDay = (index + 1) % daysCount;
            timelineDays[targetDay].gems.push(gem);
        });
    }

    // 4. Cultural Experiences distributed
    if (data.experiences && data.experiences.length > 0) {
        data.experiences.forEach((exp, index) => {
            const targetDay = (index + 2) % daysCount;
            timelineDays[targetDay].experiences.push(exp);
        });
    }

    // 5. Events distributed
    if (data.events && data.events.length > 0) {
        data.events.forEach((evt, index) => {
            const targetDay = (index + 1) % daysCount;
            timelineDays[targetDay].events.push(evt);
        });
    }

    // Render each day card
    timelineFlow.innerHTML = timelineDays.map(day => {
        const dayStr = day.dayNum.toString().padStart(2, "0");
        
        let subItemsHtml = "";
        const subItems = [];

        day.destinations.forEach(dest => {
            subItems.push(`
                <div class="timeline-sub-item">
                    <span class="timeline-card-meta">Curated Base</span>
                    <h4 class="timeline-sub-title">${dest.name}</h4>
                    <p class="timeline-sub-desc">${dest.match_reason}</p>
                </div>
            `);
        });

        day.heritage.forEach(site => {
            subItems.push(`
                <div class="timeline-sub-item">
                    <span class="timeline-card-meta">Heritage Site</span>
                    <h4 class="timeline-sub-title">${site.name}</h4>
                    <p class="timeline-sub-desc"><strong>Significance:</strong> ${site.significance}<br><strong>Respectful engagement:</strong> ${site.how_to_engage}</p>
                </div>
            `);
        });

        day.gems.forEach(gem => {
            subItems.push(`
                <div class="timeline-sub-item">
                    <span class="timeline-card-meta">Hidden Gem</span>
                    <h4 class="timeline-sub-title">${gem.name} (in ${gem.location})</h4>
                    <p class="timeline-sub-desc">${gem.description}<br><strong>Local Tip:</strong> ${gem.local_tip}</p>
                </div>
            `);
        });

        day.experiences.forEach(exp => {
            subItems.push(`
                <div class="timeline-sub-item">
                    <span class="timeline-card-meta">Local Experience (${exp.type})</span>
                    <h4 class="timeline-sub-title">${exp.name}</h4>
                    <p class="timeline-sub-desc">${exp.description}<br><strong>Cost:</strong> ${exp.budget_estimate} · <strong>Booking:</strong> ${exp.booking_tip}</p>
                </div>
            `);
        });

        day.events.forEach(evt => {
            subItems.push(`
                <div class="timeline-sub-item">
                    <span class="timeline-card-meta">Event (${evt.timing})</span>
                    <h4 class="timeline-sub-title">${evt.name}</h4>
                    <p class="timeline-sub-desc">${evt.description}<br><strong>Significance:</strong> ${evt.traveler_relevance}</p>
                </div>
            `);
        });

        if (subItems.length > 0) {
            subItemsHtml = `
                <div class="timeline-sub-grid">
                    ${subItems.join("")}
                </div>
            `;
        }

        return `
            <div class="timeline-item">
                <div class="timeline-marker" aria-label="Day ${day.dayNum}">Day ${dayStr}</div>
                <div class="timeline-content">
                    <h3 class="timeline-title">${day.title}</h3>
                    <p class="timeline-desc">${day.desc}</p>
                    ${subItemsHtml}
                </div>
            </div>
        `;
    }).join("");

    // Render story
    if (data.story && data.story.narrative) {
        storySegment.classList.remove("hidden");
        storyText.textContent = data.story.narrative;
    } else {
        storySegment.classList.add("hidden");
    }

    resultsState.scrollIntoView({ behavior: "smooth", block: "start" });
}
