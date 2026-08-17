/**
 * AI BID CAPTURE AGENT - DASHBOARD CONTROLLER
 */

const API_BASE = ""; // Relative to same origin (served by FastAPI)

let currentOpportunities = [];
let activeOpportunity = null;
let activeProfile = null;
let allProfiles = [];
let searchDebounceTimeout = null;

document.addEventListener("DOMContentLoaded", () => {
    initEventListeners();
    loadDashboardStats();
    loadAllProfiles();
    loadOpportunities();
});

function initEventListeners() {
    // Search input
    const searchInput = document.getElementById("searchInput");
    const btnClearSearch = document.getElementById("btnClearSearch");

    searchInput.addEventListener("input", (e) => {
        btnClearSearch.style.display = e.target.value ? "block" : "none";
        clearTimeout(searchDebounceTimeout);
        searchDebounceTimeout = setTimeout(() => {
            loadOpportunities();
        }, 300);
    });

    btnClearSearch.addEventListener("click", () => {
        searchInput.value = "";
        btnClearSearch.style.display = "none";
        loadOpportunities();
    });

    // Segmented Source Filter
    const sourceBtns = document.querySelectorAll("#sourceTypeFilter .seg-btn");
    sourceBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            sourceBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            loadOpportunities();
        });
    });

    // Dropdown filters
    document.getElementById("naicsFilter").addEventListener("change", loadOpportunities);
    document.getElementById("fitFilter").addEventListener("change", loadOpportunities);
    document.getElementById("statusFilter").addEventListener("change", loadOpportunities);
    document.getElementById("sortBySelect").addEventListener("change", loadOpportunities);

    // Export CSV
    document.getElementById("btnExportCsv").addEventListener("click", () => {
        const source_type = getActiveSourceType();
        const url = `${API_BASE}/api/opportunities/export?format=csv${source_type !== "ALL" ? `&source_type=${source_type}` : ""}`;
        window.open(url, "_blank");
    });

    // Capture Run Modal
    const btnTriggerCapture = document.getElementById("btnTriggerCapture");
    const captureModal = document.getElementById("captureModal");
    const btnCloseCaptureModal = document.getElementById("btnCloseCaptureModal");
    const btnCancelCapture = document.getElementById("btnCancelCapture");
    const btnStartCapture = document.getElementById("btnStartCapture");

    btnTriggerCapture.addEventListener("click", () => {
        captureModal.style.display = "flex";
        document.getElementById("captureProgress").style.display = "none";
        btnStartCapture.disabled = false;
    });

    [btnCloseCaptureModal, btnCancelCapture].forEach(btn => {
        btn.addEventListener("click", () => {
            captureModal.style.display = "none";
        });
    });

    btnStartCapture.addEventListener("click", executeCaptureRun);

    // Profile Modal
    const btnOpenProfile = document.getElementById("btnOpenProfile");
    const profileModal = document.getElementById("profileModal");
    const btnCloseProfileModal = document.getElementById("btnCloseProfileModal");
    const btnCancelProfile = document.getElementById("btnCancelProfile");
    const btnSaveProfile = document.getElementById("btnSaveProfile");

    btnOpenProfile.addEventListener("click", () => {
        loadUserProfile();
        profileModal.style.display = "flex";
    });

    [btnCloseProfileModal, btnCancelProfile].forEach(btn => {
        btn.addEventListener("click", () => {
            profileModal.style.display = "none";
        });
    });

    btnSaveProfile.addEventListener("click", saveUserProfile);

    // Capability Deck Upload Handlers
    const deckFileInput = document.getElementById("deckFileInput");
    const btnSelectDeckFile = document.getElementById("btnSelectDeckFile");
    const btnUploadDeck = document.getElementById("btnUploadDeck");
    const selectedDeckFileName = document.getElementById("selectedDeckFileName");

    btnSelectDeckFile.addEventListener("click", () => {
        deckFileInput.click();
    });

    deckFileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            selectedDeckFileName.textContent = file.name;
            btnUploadDeck.style.display = "inline-flex";
        }
    });

    btnUploadDeck.addEventListener("click", uploadCapabilityDeckFile);

    // Re-score pipeline button
    document.getElementById("btnRescorePipeline").addEventListener("click", rescoreAllOpportunities);

    // RFP Detail Modal Close
    document.getElementById("btnCloseDetailModal").addEventListener("click", () => {
        document.getElementById("rfpDetailModal").style.display = "none";
        activeOpportunity = null;
    });

    // Pursuit decision buttons
    const statusBtns = document.querySelectorAll(".status-btn-group .status-btn");
    statusBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            if (!activeOpportunity) return;
            const newStatus = btn.getAttribute("data-status");
            updateOpportunityStatus(activeOpportunity.id, newStatus);
        });
    });

    // AI Chat in detail modal
    document.getElementById("btnSendChat").addEventListener("click", sendChatQuestion);
    document.getElementById("chatInput").addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendChatQuestion();
    });
}

function getActiveSourceType() {
    const activeBtn = document.querySelector("#sourceTypeFilter .seg-btn.active");
    return activeBtn ? activeBtn.getAttribute("data-value") : "ALL";
}

async function loadDashboardStats() {
    try {
        const res = await fetch(`${API_BASE}/api/opportunities/stats`);
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("kpiTotalRfps").textContent = data.total_rfps;
        document.getElementById("kpiFederalRfps").textContent = data.federal_rfps;
        document.getElementById("kpiSledRfps").textContent = data.sled_rfps;
        document.getElementById("kpiAvgFit").textContent = `${data.avg_fit_score}%`;
        document.getElementById("kpiHighMatches").innerHTML = `<i class="fa-solid fa-star"></i> ${data.high_match_rfps} High Matches`;
    } catch (e) {
        console.error("Failed loading stats:", e);
    }
}

async function loadAllProfiles() {
    try {
        const res = await fetch(`${API_BASE}/api/profile/all`);
        if (!res.ok) return;
        allProfiles = await res.json();
        renderNavProfileSelector();
    } catch (e) {
        console.error("Failed loading all profiles:", e);
    }
}

function renderNavProfileSelector() {
    const navActions = document.querySelector(".nav-actions");
    let selector = document.getElementById("navProfileSelector");
    if (!selector) {
        selector = document.createElement("div");
        selector.className = "profile-pill-selector";
        selector.id = "navProfileSelector";
        selector.innerHTML = `
            <i class="fa-solid fa-building text-cyan"></i>
            <select id="profileDropdown" title="Switch Company Capability Deck"></select>
        `;
        navActions.insertBefore(selector, document.getElementById("btnOpenProfile"));
    }

    const dropdown = document.getElementById("profileDropdown");
    dropdown.innerHTML = "";
    allProfiles.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.company_name} ${p.cage_code ? `[CAGE: ${p.cage_code}]` : ""}`;
        if (p.is_active) opt.selected = true;
        dropdown.appendChild(opt);
    });

    dropdown.onchange = (e) => {
        switchProfile(e.target.value);
    };
}

async function switchProfile(profileId) {
    showToast("Switching capability profile & re-scoring pipeline...");
    try {
        const res = await fetch(`${API_BASE}/api/profile/switch/${profileId}`, {
            method: "POST"
        });
        if (!res.ok) throw new Error("Failed to switch profile");
        const data = await res.json();
        activeProfile = data.active_profile;

        showToast(data.message);
        loadDashboardStats();
        loadOpportunities();
        loadAllProfiles();
    } catch (e) {
        showToast("Error switching profile", "error");
    }
}

async function loadOpportunities() {
    const grid = document.getElementById("rfpGrid");
    grid.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Filtering procurement opportunities...</p>
        </div>
    `;

    const q = document.getElementById("searchInput").value.trim();
    const source_type = getActiveSourceType();
    const naics = document.getElementById("naicsFilter").value;
    const min_fit_score = document.getElementById("fitFilter").value;
    const status = document.getElementById("statusFilter").value;
    const sortVal = document.getElementById("sortBySelect").value.split(":");
    const sort_by = sortVal[0];
    const sort_order = sortVal[1];

    const params = new URLSearchParams();
    if (q) params.append("q", q);
    if (source_type !== "ALL") params.append("source_type", source_type);
    if (naics) params.append("naics_code", naics);
    if (min_fit_score && min_fit_score !== "0") params.append("min_fit_score", min_fit_score);
    if (status && status !== "ALL") params.append("status", status);
    params.append("sort_by", sort_by);
    params.append("sort_order", sort_order);

    try {
        const res = await fetch(`${API_BASE}/api/opportunities?${params.toString()}`);
        if (!res.ok) throw new Error("Failed to fetch opportunities");
        const data = await res.json();
        currentOpportunities = data;

        document.getElementById("resultsCount").textContent = data.length;
        renderOpportunities(data);
    } catch (err) {
        console.error(err);
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 2.5rem; color: var(--rose);"></i>
                <h4>Error loading opportunities</h4>
                <p>Could not connect to the backend database.</p>
            </div>
        `;
    }
}

function renderOpportunities(opps) {
    const grid = document.getElementById("rfpGrid");
    if (!opps || opps.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-radar" style="font-size: 2.8rem; color: var(--text-dim);"></i>
                <h4>No matching RFPs found</h4>
                <p>Try adjusting your search keywords, NAICS filters, or minimum fit score.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = "";
    opps.forEach(opp => {
        const card = document.createElement("div");
        card.className = "rfp-card";
        card.id = `card-${opp.id}`;

        const isFederal = opp.source_type === "FEDERAL";
        const sourceBadgeClass = isFederal ? "badge-federal" : "badge-sled";
        const sourceLabel = isFederal ? "Federal • SAM.gov" : `SLED • ${opp.source.replace("_", " ")}`;

        // Fit score style
        let scoreClass = "fit-medium";
        if (opp.fit_score >= 85) scoreClass = "fit-high";
        else if (opp.fit_score < 70) scoreClass = "fit-low";

        // Due date calculation
        let dueBadgeText = opp.due_date ? `Due: ${opp.due_date}` : "Due: Open";
        if (opp.due_date) {
            const daysLeft = calculateDaysRemaining(opp.due_date);
            if (daysLeft !== null) {
                if (daysLeft < 0) dueBadgeText = "Expired";
                else if (daysLeft === 0) dueBadgeText = "Due Today!";
                else dueBadgeText = `In ${daysLeft} days (${opp.due_date})`;
            }
        }

        const summaryPreview = opp.ai_summary || opp.description_raw || "AI synthesis in progress...";

        card.innerHTML = `
            <div class="card-top">
                <div class="card-badges">
                    <span class="badge-source ${sourceBadgeClass}">${sourceLabel}</span>
                    ${opp.naics_code ? `<span class="badge-naics">NAICS ${opp.naics_code}</span>` : ""}
                    ${opp.state && opp.state !== "US" ? `<span class="badge-naics">${opp.state}</span>` : ""}
                </div>
                <div class="fit-score-badge ${scoreClass}">
                    <i class="fa-solid fa-sparkles"></i>
                    <span>${opp.fit_score}%</span>
                </div>
            </div>

            <div class="card-title" title="${escapeHtml(opp.title)}">${escapeHtml(opp.title)}</div>
            <div class="card-agency"><i class="fa-solid fa-building-columns"></i> ${escapeHtml(opp.agency)}</div>

            <div class="card-summary-preview">${escapeHtml(summaryPreview)}</div>

            <div class="card-meta-row">
                <div class="meta-due"><i class="fa-regular fa-clock"></i> ${dueBadgeText}</div>
                ${opp.set_aside && opp.set_aside !== "None" ? `<div class="meta-setaside"><i class="fa-solid fa-handshake-angle"></i> ${escapeHtml(opp.set_aside)}</div>` : ""}
                ${opp.estimated_value ? `<div class="meta-val"><i class="fa-solid fa-sack-dollar"></i> ${escapeHtml(opp.estimated_value)}</div>` : ""}
            </div>

            <div class="card-footer">
                <button class="btn-inspect" onclick="openOpportunityDetail('${opp.id}')">
                    <i class="fa-solid fa-file-waveform"></i> Inspect RFP & AI SOW
                </button>
            </div>
        `;

        grid.appendChild(card);
    });
}

function calculateDaysRemaining(dueDateStr) {
    if (!dueDateStr) return null;
    try {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const due = new Date(dueDateStr);
        const diffTime = due.getTime() - today.getTime();
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    } catch (e) {
        return null;
    }
}

function openOpportunityDetail(id) {
    const opp = currentOpportunities.find(o => o.id === id);
    if (!opp) return;

    activeOpportunity = opp;
    const modal = document.getElementById("rfpDetailModal");

    // Header & Badges
    const isFederal = opp.source_type === "FEDERAL";
    const sourceLabel = isFederal ? "Federal • SAM.gov" : `SLED • ${opp.source.replace("_", " ")}`;
    document.getElementById("modalBadges").innerHTML = `
        <span class="badge-source ${isFederal ? "badge-federal" : "badge-sled"}">${sourceLabel}</span>
        <span class="badge-naics">NAICS: ${opp.naics_code || "N/A"}</span>
        <span class="badge-naics">Status: ${opp.status}</span>
    `;

    document.getElementById("modalTitle").textContent = opp.title;
    document.getElementById("modalAgency").textContent = opp.agency;

    // Meta Banner
    document.getElementById("modalSolNum").textContent = opp.solicitation_number || "N/A";
    document.getElementById("modalDueDate").textContent = opp.due_date || "Not specified";
    document.getElementById("modalNaics").textContent = `${opp.naics_code || "N/A"} (${opp.naics_title || "General"})`;
    document.getElementById("modalSetAside").textContent = opp.set_aside || "None";
    document.getElementById("modalEstValue").textContent = opp.estimated_value || "Undisclosed";

    // AI Summary & Rationale
    document.getElementById("modalAiSummary").textContent = opp.ai_summary || opp.description_raw || "No summary available.";
    document.getElementById("modalFitRationale").textContent = opp.fit_rationale || "Calculated according to targeted NAICS codes and capabilities.";

    // Scope & Deliverables
    const deliverablesList = document.getElementById("modalDeliverables");
    deliverablesList.innerHTML = "";
    const deliverables = opp.sow_deliverables || [];
    if (deliverables.length > 0) {
        deliverables.forEach(item => {
            const li = document.createElement("li");
            li.textContent = typeof item === "string" ? item : JSON.stringify(item);
            deliverablesList.appendChild(li);
        });
    } else {
        deliverablesList.innerHTML = `<li>Standard lifecycle solution engineering, implementation, and maintenance.</li>`;
    }

    // Mandatory Qualifications
    const qualList = document.getElementById("modalQualifications");
    qualList.innerHTML = "";
    const quals = opp.mandatory_qualifications || [];
    if (quals.length > 0) {
        quals.forEach(q => {
            const li = document.createElement("li");
            li.textContent = typeof q === "string" ? q : JSON.stringify(q);
            qualList.appendChild(li);
        });
    } else {
        qualList.innerHTML = `<li>Past performance on similar contracts, active business registration, and qualified staff.</li>`;
    }

    // Compliance Checklist
    const compContainer = document.getElementById("modalCompliance");
    compContainer.innerHTML = "";
    const compliance = opp.compliance_checklist || [];
    if (compliance.length > 0) {
        compliance.forEach(c => {
            const itemDiv = document.createElement("div");
            itemDiv.className = "compliance-item";
            const itemName = typeof c === "string" ? c : (c.item || JSON.stringify(c));
            const status = c.status || "Pending";
            let tagClass = "comp-pend";
            if (status.toLowerCase().includes("ready") || status.toLowerCase().includes("verified")) tagClass = "comp-ready";
            else if (status.toLowerCase().includes("progress")) tagClass = "comp-prog";

            itemDiv.innerHTML = `
                <span>${escapeHtml(itemName)}</span>
                <span class="compliance-tag ${tagClass}">${status}</span>
            `;
            compContainer.appendChild(itemDiv);
        });
    } else {
        compContainer.innerHTML = `<div class="compliance-item"><span>Standard Technical & Pricing Volumes</span><span class="compliance-tag comp-ready">Ready</span></div>`;
    }

    // Evaluation Factors
    const evalContainer = document.getElementById("modalEvaluation");
    evalContainer.innerHTML = "";
    const evals = opp.evaluation_criteria || [];
    if (evals.length > 0) {
        evals.forEach(e => {
            const card = document.createElement("div");
            card.className = "eval-card";
            const factor = e.factor || (typeof e === "string" ? e : "Evaluation Factor");
            const weight = e.weight || "30%";
            card.innerHTML = `
                <span>${escapeHtml(factor)}</span>
                <span class="eval-weight">${weight}</span>
            `;
            evalContainer.appendChild(card);
        });
    } else {
        evalContainer.innerHTML = `
            <div class="eval-card"><span>Technical Approach</span><span class="eval-weight">40%</span></div>
            <div class="eval-card"><span>Past Performance</span><span class="eval-weight">30%</span></div>
            <div class="eval-card"><span>Evaluated Price</span><span class="eval-weight">30%</span></div>
        `;
    }

    // Attachments & Source
    const attContainer = document.getElementById("modalAttachments");
    attContainer.innerHTML = "";
    if (opp.source_url) {
        const srcBtn = document.createElement("a");
        srcBtn.href = opp.source_url;
        srcBtn.target = "_blank";
        srcBtn.className = "att-link";
        srcBtn.innerHTML = `<i class="fa-solid fa-arrow-up-right-from-square"></i> View on Official Portal`;
        attContainer.appendChild(srcBtn);
    }
    (opp.attachments || []).forEach(att => {
        const a = document.createElement("a");
        a.href = att.url || "#";
        a.target = "_blank";
        a.className = "att-link";
        a.innerHTML = `<i class="fa-solid fa-file-pdf"></i> ${escapeHtml(att.name)}`;
        attContainer.appendChild(a);
    });

    // Fit score sidebar
    document.getElementById("modalFitScore").textContent = `${opp.fit_score}%`;

    // Active status button
    const statusBtns = document.querySelectorAll(".status-btn-group .status-btn");
    statusBtns.forEach(btn => {
        if (btn.getAttribute("data-status") === opp.status) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Reset Chat Messages
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = `
        <div class="chat-bubble ai">
            Ask me anything about <strong>${escapeHtml(opp.title)}</strong> (e.g. key deadlines, mandatory qualifications, or submission requirements)!
        </div>
    `;

    modal.style.display = "flex";
}

async function updateOpportunityStatus(id, newStatus) {
    try {
        const res = await fetch(`${API_BASE}/api/opportunities/${id}/status?status=${newStatus}`, {
            method: "PATCH"
        });
        if (!res.ok) throw new Error("Failed to update status");

        // Update local object
        if (activeOpportunity) activeOpportunity.status = newStatus;
        const target = currentOpportunities.find(o => o.id === id);
        if (target) target.status = newStatus;

        // Update button states
        const statusBtns = document.querySelectorAll(".status-btn-group .status-btn");
        statusBtns.forEach(btn => {
            if (btn.getAttribute("data-status") === newStatus) btn.classList.add("active");
            else btn.classList.remove("active");
        });

        showToast(`Status updated to: ${newStatus}`);
        loadDashboardStats();
    } catch (e) {
        console.error(e);
        showToast("Error updating status", "error");
    }
}

async function sendChatQuestion() {
    if (!activeOpportunity) return;
    const input = document.getElementById("chatInput");
    const question = input.value.trim();
    if (!question) return;

    input.value = "";
    appendChatMessage(question, "user");

    const typingBubble = appendChatMessage("Analyzing RFP...", "ai");

    try {
        const res = await fetch(`${API_BASE}/api/ai/ask/${activeOpportunity.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });
        const data = await res.json();
        typingBubble.textContent = data.answer || "No response received.";
    } catch (e) {
        typingBubble.textContent = "Could not communicate with AI agent.";
    }
}

function askPresetQuestion(q) {
    document.getElementById("chatInput").value = q;
    sendChatQuestion();
}

function appendChatMessage(text, sender) {
    const container = document.getElementById("chatMessages");
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;
    bubble.textContent = text;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return bubble;
}

async function executeCaptureRun() {
    const checkboxes = document.querySelectorAll('input[name="portalSource"]:checked');
    const sources = Array.from(checkboxes).map(cb => cb.value);
    const dueWindow = parseInt(document.getElementById("captureDueWindow").value) || 45;

    const btnStart = document.getElementById("btnStartCapture");
    const progress = document.getElementById("captureProgress");
    const statusText = document.getElementById("scannerStatus");

    btnStart.disabled = true;
    progress.style.display = "flex";
    statusText.textContent = `Querying ${sources.length} portals for solicitations...`;

    try {
        const res = await fetch(`${API_BASE}/api/capture/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sources: sources.length > 0 ? sources : ["ALL"],
                due_window_days: dueWindow
            })
        });

        const data = await res.json();
        showToast(data.message || "Capture run completed!");
        document.getElementById("captureModal").style.display = "none";
        loadDashboardStats();
        loadOpportunities();
    } catch (e) {
        console.error(e);
        showToast("Capture failed", "error");
    } finally {
        btnStart.disabled = false;
        progress.style.display = "none";
    }
}

async function loadUserProfile() {
    try {
        const res = await fetch(`${API_BASE}/api/profile`);
        if (!res.ok) return;
        const profile = await res.json();
        activeProfile = profile;

        document.getElementById("profileCompanyName").value = profile.company_name || "";
        document.getElementById("profileCapabilities").value = profile.capabilities_summary || "";
        document.getElementById("profileNaics").value = (profile.target_naics || []).join(", ");
        document.getElementById("profileKeywords").value = (profile.target_keywords || []).join(", ");
    } catch (e) {
        console.error("Error loading profile:", e);
    }
}

async function uploadCapabilityDeckFile() {
    const fileInput = document.getElementById("deckFileInput");
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast("Please choose a file first", "error");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    const btnUpload = document.getElementById("btnUploadDeck");
    btnUpload.disabled = true;
    btnUpload.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Parsing with AI...`;

    try {
        const res = await fetch(`${API_BASE}/api/profile/upload-deck`, {
            method: "POST",
            body: formData
        });
        if (!res.ok) throw new Error("Deck upload failed");
        const data = await res.json();

        showToast(data.message || "Capability Deck parsed successfully!");
        loadUserProfile();
        loadAllProfiles();
        loadOpportunities();
        loadDashboardStats();

        document.getElementById("selectedDeckFileName").textContent = "No file chosen";
        btnUpload.style.display = "none";
    } catch (e) {
        console.error(e);
        showToast("Error processing capability deck", "error");
    } finally {
        btnUpload.disabled = false;
        btnUpload.innerHTML = `<i class="fa-solid fa-sparkles"></i> AI Parse & Extract Deck`;
    }
}

async function rescoreAllOpportunities() {
    showToast("Re-scoring all active RFPs against current capability profile...");
    try {
        const res = await fetch(`${API_BASE}/api/profile/rescore-pipeline`, {
            method: "POST"
        });
        if (!res.ok) throw new Error("Failed to re-score");
        const data = await res.json();
        showToast(data.message || "Pipeline re-scored!");
        loadOpportunities();
        loadDashboardStats();
    } catch (e) {
        showToast("Re-scoring failed", "error");
    }
}

async function saveUserProfile() {
    const company_name = document.getElementById("profileCompanyName").value.trim();
    const capabilities_summary = document.getElementById("profileCapabilities").value.trim();
    const naicsStr = document.getElementById("profileNaics").value.trim();
    const kwStr = document.getElementById("profileKeywords").value.trim();

    const target_naics = naicsStr ? naicsStr.split(",").map(s => s.trim()) : [];
    const target_keywords = kwStr ? kwStr.split(",").map(s => s.trim()) : [];

    try {
        const res = await fetch(`${API_BASE}/api/profile`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                company_name,
                capabilities_summary,
                target_naics,
                target_keywords
            })
        });
        if (!res.ok) throw new Error("Failed to save profile");

        showToast("Profile & Matching Rules updated!");
        document.getElementById("profileModal").style.display = "none";
        loadAllProfiles();
        rescoreAllOpportunities();
    } catch (e) {
        showToast("Failed to save profile", "error");
    }
}

function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `
        <i class="fa-solid ${type === 'success' ? 'fa-circle-check text-emerald' : 'fa-circle-exclamation text-rose'}"></i>
        <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
