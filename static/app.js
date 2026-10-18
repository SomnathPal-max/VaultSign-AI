// VaultSign AI - Client-side Interaction Controller
// Fully local execution, strictly communicating with 127.0.0.1

let currentReport = null;
let activeClauseFamily = null;
let currentTone = "neutral";

// DOM Elements
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const dropLabel = document.getElementById("dropLabel");
const selectedFileName = document.getElementById("selectedFileName");
const analyzeBtn = document.getElementById("analyzeBtn");
const resetBtn = document.getElementById("resetBtn");
const modelSelector = document.getElementById("modelSelector");
const loadingIndicator = document.getElementById("loadingIndicator");
const resultsSection = document.getElementById("resultsSection");
const clauseCardsContainer = document.getElementById("clauseCardsContainer");

// KPIs
const kpiTotal = document.getElementById("kpiTotal");
const kpiFlags = document.getElementById("kpiFlags");
const kpiHighRisk = document.getElementById("kpiHighRisk");
const kpiVerified = document.getElementById("kpiVerified");
const kpiDropped = document.getElementById("kpiDropped");
const reportDocName = document.getElementById("reportDocName");
const reportPages = document.getElementById("reportPages");

// Modals
const debateModal = document.getElementById("debateModal");
const closeDebateBtn = document.getElementById("closeDebateBtn");
const debateContent = document.getElementById("debateContent");
const debateClauseTitle = document.getElementById("debateClauseTitle");
const copyCompromiseBtn = document.getElementById("copyCompromiseBtn");

const pushbackModal = document.getElementById("pushbackModal");
const closePushbackBtn = document.getElementById("closePushbackBtn");
const emailClauseTitle = document.getElementById("emailClauseTitle");
const emailSubject = document.getElementById("emailSubject");
const emailBodyText = document.getElementById("emailBodyText");
const copyEmailBtn = document.getElementById("copyEmailBtn");

let activeCompromiseText = "";
let selectedFile = null;
let selectedSampleName = null;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    setupDragDrop();
    setupSampleButtons();
    setupActions();
    checkSystemStatus();
});

function checkSystemStatus() {
    fetch("/api/status")
        .then(res => res.json())
        .then(data => {
            if (data.available_models && data.available_models.length > 0) {
                // Populate model selector with live local models
                const currentVal = modelSelector.value;
                modelSelector.innerHTML = '<option value="deterministic">Deterministic Engine (Offline Baseline)</option>';
                data.available_models.forEach(m => {
                    if (!m.includes("embed") && !m.includes("bge") && !m.includes("bert")) {
                        const opt = document.createElement("option");
                        opt.value = m;
                        opt.textContent = `${m} - Ollama`;
                        modelSelector.appendChild(opt);
                    }
                });
                if (data.default_model) {
                    modelSelector.value = data.default_model;
                }
            }
        })
        .catch(() => {
            console.log("Local API status check offline fallback");
        });
}

function setupDragDrop() {
    dropZone.addEventListener("click", () => fileInput.click());
    
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add("border-indigo-500", "bg-indigo-500/10");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove("border-indigo-500", "bg-indigo-500/10");
        }, false);
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        if (dt.files.length > 0) {
            handleFileSelection(dt.files[0]);
        }
    });
}

function handleFileSelection(file) {
    selectedFile = file;
    selectedSampleName = null;
    selectedFileName.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    selectedFileName.classList.remove("hidden");
    dropLabel.innerHTML = `Loaded: <strong class="text-indigo-300">${file.name}</strong>`;
}

function setupSampleButtons() {
    document.querySelectorAll(".sample-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const sample = btn.getAttribute("data-sample");
            selectedSampleName = sample;
            selectedFile = null;
            selectedFileName.textContent = `Selected Sample: ${sample}`;
            selectedFileName.classList.remove("hidden");
            dropLabel.innerHTML = `Loaded Sample: <strong class="text-amber-300">${sample}</strong>`;
            runAnalysis();
        });
    });
}

function setupActions() {
    analyzeBtn.addEventListener("click", () => runAnalysis());

    resetBtn.addEventListener("click", () => {
        if (confirm("Wipe in-memory document session? All document text and vector chunks will be erased from RAM.")) {
            fetch("/api/reset", { method: "POST" })
                .then(r => r.json())
                .then(() => {
                    currentReport = null;
                    selectedFile = null;
                    selectedSampleName = null;
                    selectedFileName.classList.add("hidden");
                    dropLabel.textContent = "Drag and drop contract here, or browse files";
                    resultsSection.classList.add("hidden");
                    alert("Memory wiped cleanly. Zero persistent traces remain.");
                });
        }
    });

    // Close Modals
    closeDebateBtn.addEventListener("click", () => debateModal.classList.add("hidden"));
    closePushbackBtn.addEventListener("click", () => pushbackModal.classList.add("hidden"));

    // Copy Compromise Clause
    copyCompromiseBtn.addEventListener("click", () => {
        if (activeCompromiseText) {
            navigator.clipboard.writeText(activeCompromiseText).then(() => {
                const prev = copyCompromiseBtn.textContent;
                copyCompromiseBtn.textContent = "✓ Copied to Clipboard!";
                setTimeout(() => copyCompromiseBtn.textContent = prev, 2000);
            });
        }
    });

    // Copy Pushback Email
    copyEmailBtn.addEventListener("click", () => {
        const fullEmail = `SUBJECT: ${emailSubject.textContent}\n\n${emailBodyText.value}`;
        navigator.clipboard.writeText(fullEmail).then(() => {
            const prev = copyEmailBtn.textContent;
            copyEmailBtn.textContent = "✓ Copied Email!";
            setTimeout(() => copyEmailBtn.textContent = prev, 2000);
        });
    });

    // Tone switch buttons
    document.querySelectorAll(".tone-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tone-btn").forEach(b => {
                b.classList.remove("active", "bg-indigo-600", "text-white");
                b.classList.add("text-slate-400");
            });
            btn.classList.add("active", "bg-indigo-600", "text-white");
            btn.classList.remove("text-slate-400");
            currentTone = btn.getAttribute("data-tone");
            updatePushbackEmail();
        });
    });

    // Live update on input changes
    ["emailUserName", "emailClientName", "emailProjectName", "emailCustomJustification"].forEach(id => {
        document.getElementById(id).addEventListener("input", () => {
            updatePushbackEmail();
        });
    });

    // Export buttons
    document.getElementById("exportMdBtn").addEventListener("click", () => triggerExport("markdown"));
    document.getElementById("exportHtmlBtn").addEventListener("click", () => triggerExport("html"));
    document.getElementById("exportJsonBtn").addEventListener("click", () => triggerExport("json"));
}

function runAnalysis() {
    if (!selectedFile && !selectedSampleName) {
        alert("Please select a contract file or click one of the quick evaluation samples.");
        return;
    }

    loadingIndicator.classList.remove("hidden");
    resultsSection.classList.add("hidden");

    const formData = new FormData();
    if (selectedFile) {
        formData.append("file", selectedFile);
    } else if (selectedSampleName) {
        formData.append("sample_name", selectedSampleName);
    }
    
    formData.append("execution_mode", modelSelector.value === "deterministic" ? "deterministic" : "hybrid");
    formData.append("model_name", modelSelector.value);

    fetch("/api/analyze", {
        method: "POST",
        body: formData
    })
    .then(res => {
        if (!res.ok) throw new Error("Analysis failed");
        return res.json();
    })
    .then(data => {
        loadingIndicator.classList.add("hidden");
        if (data.success && data.report) {
            currentReport = data.report;
            renderResults(data.report);
        }
    })
    .catch(err => {
        loadingIndicator.classList.add("hidden");
        alert("Error analyzing contract: " + err.message);
    });
}

function renderResults(report) {
    resultsSection.classList.remove("hidden");

    reportDocName.textContent = report.filename;
    reportPages.textContent = `(${report.total_pages} page${report.total_pages > 1 ? 's' : ''})`;

    // KPIs
    kpiTotal.textContent = report.summary.total_clause_families_analyzed || 8;
    kpiFlags.textContent = report.summary.flagged_issues || 0;
    kpiHighRisk.textContent = report.summary.high_risk_issues || 0;
    kpiDropped.textContent = report.dropped_hallucinations_count || 0;
    
    const verifPct = report.summary.flagged_issues > 0 ? "100%" : "Clean";
    kpiVerified.textContent = verifPct;

    // Render 8 Clause Cards
    clauseCardsContainer.innerHTML = "";

    report.flags.forEach(flag => {
        const isFlagged = flag.status === "FLAGGED";
        const card = document.createElement("div");
        card.className = `clause-card p-5 rounded-2xl border transition-all ${
            isFlagged 
                ? "bg-slate-900/90 border-red-500/50 shadow-lg shadow-red-500/5 hover:border-red-400" 
                : "bg-slate-900/40 border-slate-800 hover:border-slate-700 opacity-90"
        }`;

        let content = `
            <div class="flex items-center justify-between gap-2 mb-3">
                <div class="flex items-center gap-2">
                    <span class="text-base">${isFlagged ? '🚨' : '🛡️'}</span>
                    <h4 class="text-sm font-bold text-white">${flag.family_label}</h4>
                </div>
                <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${
                    isFlagged 
                        ? (flag.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30')
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }">
                    ${isFlagged ? `${flag.risk_level} RISK` : 'NOT DETECTED'}
                </span>
            </div>
        `;

        if (isFlagged) {
            content += `
                <div class="mb-3 p-3 bg-slate-950 border-l-2 border-red-500 rounded font-mono text-xs text-red-200/90 leading-relaxed verbatim-quote">
                    <div class="text-[10px] text-slate-500 font-sans uppercase mb-1 flex items-center justify-between">
                        <span>Verified Source Quote &bull; Page ${flag.page_number || 1}</span>
                        <span class="text-emerald-400">✓ Verbatim Match</span>
                    </div>
                    &ldquo;${flag.verbatim_quote}&rdquo;
                </div>
                <p class="text-xs text-slate-300 mb-2 leading-relaxed">
                    <strong class="text-slate-200">The Trap:</strong> ${flag.plain_english_explanation}
                </p>
                <div class="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl mb-4 text-xs text-indigo-300">
                    <strong class="text-indigo-200">Recommended Ask:</strong> ${flag.suggested_ask}
                </div>
                <div class="flex items-center gap-2 pt-2 border-t border-slate-800">
                    <button class="debate-btn flex-1 py-1.5 px-3 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-lg transition-all flex items-center justify-center gap-1.5" data-family="${flag.clause_family}">
                        <span>⚖️ Agent Debate (Pro)</span>
                    </button>
                    <button class="pushback-btn flex-1 py-1.5 px-3 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white rounded-lg shadow-md transition-all flex items-center justify-center gap-1.5" data-family="${flag.clause_family}">
                        <span>✉️ Draft Pushback</span>
                    </button>
                </div>
            `;
        } else {
            content += `
                <p class="text-xs text-slate-400 italic mb-2">
                    ${flag.plain_english_explanation}
                </p>
                <p class="text-[11px] text-slate-500">
                    Standard Freelancer Ask: ${flag.suggested_ask}
                </p>
            `;
        }

        card.innerHTML = content;
        clauseCardsContainer.appendChild(card);
    });

    // Attach click listeners to cards
    document.querySelectorAll(".debate-btn").forEach(b => {
        b.addEventListener("click", () => openDebateModal(b.getAttribute("data-family")));
    });
    document.querySelectorAll(".pushback-btn").forEach(b => {
        b.addEventListener("click", () => openPushbackModal(b.getAttribute("data-family")));
    });
}

function openDebateModal(familyKey) {
    const flag = currentReport.flags.find(f => f.clause_family === familyKey);
    if (!flag) return;

    debateClauseTitle.textContent = `Debating: ${flag.family_label}`;
    debateContent.innerHTML = `
        <div class="py-8 text-center text-slate-400">
            <div class="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            Spawning Advocate, Corporate Counsel, and Mediator personas...
        </div>
    `;
    debateModal.classList.remove("hidden");

    fetch("/api/simulate-debate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            clause_family: familyKey,
            model_name: modelSelector.value
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && data.debate) {
            renderDebate(data.debate);
        }
    })
    .catch(err => {
        debateContent.innerHTML = `<p class="text-rose-400">Simulation error: ${err.message}</p>`;
    });
}

function renderDebate(debate) {
    activeCompromiseText = debate.compromise_clause;
    let html = `
        <div class="mb-4 p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300">
            <span class="text-slate-500 uppercase font-mono text-[10px]">Contract Clause Under Review:</span>
            <p class="mt-1 font-mono text-red-300">&ldquo;${debate.original_quote}&rdquo;</p>
        </div>
        <div class="space-y-4">
    `;

    debate.turns.forEach(turn => {
        let roleBadge = "bg-indigo-600 text-white";
        let roleIcon = "🛡️";
        let cardBg = "bg-slate-950 border-slate-800";

        if (turn.role.includes("Counsel")) {
            roleBadge = "bg-amber-600 text-white";
            roleIcon = "🏢";
        } else if (turn.role.includes("Mediator")) {
            roleBadge = "bg-emerald-600 text-white";
            roleIcon = "🤝";
            cardBg = "bg-emerald-950/20 border-emerald-500/30";
        }

        html += `
            <div class="p-4 rounded-xl border ${cardBg}">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <span class="px-2.5 py-0.5 rounded text-xs font-bold ${roleBadge} flex items-center gap-1">
                            <span>${roleIcon}</span> ${turn.role}
                        </span>
                    </div>
                    <span class="text-[10px] text-slate-400 font-mono">${turn.guardrail}</span>
                </div>
                <p class="text-xs text-slate-200 leading-relaxed mb-2">${turn.statement}</p>
                ${turn.arguments && turn.arguments.length ? `
                    <div class="flex flex-wrap gap-1.5 mt-2">
                        ${turn.arguments.map(arg => `<span class="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-300">${arg}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    });

    html += `
        </div>
        <div class="mt-6 p-4 bg-emerald-950/40 border-2 border-emerald-500/40 rounded-xl">
            <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                    ✨ Synthesized Compromise Clause Language
                </span>
                <span class="text-[10px] text-emerald-300/80 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Ready to Review</span>
            </div>
            <p class="text-xs font-mono text-emerald-200 bg-slate-950 p-3 rounded-lg border border-emerald-500/20 leading-relaxed">
                ${debate.compromise_clause}
            </p>
        </div>
    `;

    debateContent.innerHTML = html;
}

function openPushbackModal(familyKey) {
    activeClauseFamily = familyKey;
    const flag = currentReport.flags.find(f => f.clause_family === familyKey);
    emailClauseTitle.textContent = `Counter-Offer: ${flag ? flag.family_label : familyKey}`;
    pushbackModal.classList.remove("hidden");
    updatePushbackEmail();
}

function updatePushbackEmail() {
    if (!activeClauseFamily) return;

    fetch("/api/generate-pushback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            clause_family: activeClauseFamily,
            tone: currentTone,
            user_name: document.getElementById("emailUserName").value || "Alex Rivera",
            client_name: document.getElementById("emailClientName").value || "Sarah Jenkins",
            project_name: document.getElementById("emailProjectName").value || "Contract Engagement",
            custom_justification: document.getElementById("emailCustomJustification").value || null
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && data.email) {
            emailSubject.textContent = data.email.subject;
            emailBodyText.value = data.email.body;
        }
    });
}

function triggerExport(format) {
    if (!currentReport) return;
    
    fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            format: format,
            user_name: "Freelancer",
            client_name: "Client"
        })
    })
    .then(res => res.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const ext = format === "html" ? "html" : format === "json" ? "json" : "md";
        a.download = `VaultSign_Audit_${currentReport.filename}.${ext}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    });
}
