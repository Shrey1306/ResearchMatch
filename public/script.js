/* ───────────────────────────
   Global state
──────────────────────────── */
let allResearchers = [];
let uniqueResearchAreas = new Set();
let selectedResearchAreas = new Set();
let currentModel = "scraping"; // default LLM source

/* ───────────────────────────
   Helpers
──────────────────────────── */
function cleanResearchArea(area = "") {
  const abbreviations = {
    ai: "Artificial Intelligence",
    ml: "Machine Learning",
    nlp: "Natural Language Processing",
    hci: "Human‑Computer Interaction",
    iot: "Internet of Things",
    ar: "Augmented Reality",
    vr: "Virtual Reality",
    xr: "Extended Reality",
    os: "Operating Systems",
    db: "Database",
    ui: "User Interface",
    ux: "User Experience",
  };
  const lowercase = new Set(
    "a an the and or but nor for yet so at by in of on to up as".split(" ")
  );

  return area
    .toLowerCase()
    .trim()
    .replace(/[&/\\#,+()$~%.'":*?<>{}]/g, " ")
    .replace(/\s+/g, " ")
    .split(" ")
    .map((w) => {
      if (abbreviations[w]) return abbreviations[w];
      return lowercase.has(w) ? w : w.charAt(0).toUpperCase() + w.slice(1);
    })
    .join(" ")
    .replace(/^(and|or|&)\s+/i, "")
    .replace(/\s+(and|or|&)$/i, "")
    .trim();
}

function researcherAreas(r) {
  return (r.research_areas?.[currentModel] || []).map(cleanResearchArea);
}

/* ───────────────────────────
   Build topic multiselect
──────────────────────────── */
function rebuildTopics() {
  uniqueResearchAreas.clear();
  const seen = new Set();

  allResearchers.forEach((r) =>
    researcherAreas(r).forEach((a) => {
      if (a && !seen.has(a)) {
        seen.add(a);
        uniqueResearchAreas.add(a);
      }
    })
  );
  populateResearchAreasDropdown();
}

function highlightText(text, query) {
  if (!query) return text;
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<span class="highlight">$1</span>');
}

function filterAndPopulateAreas(searchQuery = '', preserveScroll = false) {
  const box = document.getElementById("topicsContainer");
  const existingSelect = document.getElementById("researchAreasSelect");
  const scrollPos = existingSelect?.scrollTop || 0;

  box.innerHTML = "";

  const sel = document.createElement("select");
  sel.id = "researchAreasSelect";
  sel.multiple = true;
  sel.size = 15;

  const tip = document.createElement("option");
  tip.disabled = true;
  tip.textContent = "↑↓ navigate, space select, or click";
  sel.appendChild(tip);

  // Filter and sort areas
  const filteredAreas = Array.from(uniqueResearchAreas)
    .filter((area) => !searchQuery || area.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort();

  // Show message if no results
  if (filteredAreas.length === 0 && searchQuery) {
    const noResults = document.createElement("option");
    noResults.disabled = true;
    noResults.textContent = "No matching research areas found";
    sel.appendChild(noResults);
  }

  // Add filtered areas with highlighting
  filteredAreas.forEach((area) => {
    const op = document.createElement("option");
    op.value = area;
    op.innerHTML = searchQuery ? highlightText(area, searchQuery) : area;
    op.selected = selectedResearchAreas.has(area);
    sel.appendChild(op);
  });

  // Preserve scroll and handle keyboard navigation without auto-scroll
  sel.addEventListener("keydown", (e) => {
    const currentScroll = sel.scrollTop;

    // space = toggle selection
    if (e.code === "Space") {
      e.preventDefault();
      toggleOptionSelection(sel.options[sel.selectedIndex]);
    }

    // up/down = move focus without scrolling
    if (e.code === "ArrowUp" || e.code === "ArrowDown") {
      e.preventDefault();
      const dir = e.code === "ArrowUp" ? -1 : 1;
      let idx = sel.selectedIndex + dir;
      idx = Math.max(1, Math.min(sel.options.length - 1, idx));
      sel.selectedIndex = idx;
    }

    // restore the scroll
    requestAnimationFrame(() => {
      sel.scrollTop = currentScroll;
    });
  });

  // Prevent click from jumping scroll
  sel.addEventListener("mousedown", (e) => {
    e.preventDefault();
    const op = e.target.closest("option");
    if (op && !op.disabled) toggleOptionSelection(op);
  });

  box.appendChild(sel);

  // Restore scroll position if needed
  if (preserveScroll && existingSelect) {
    sel.scrollTop = scrollPos;
  }
}

function populateResearchAreasDropdown() {
  filterAndPopulateAreas('', true);  // Pass true to preserve scroll
}

/* ───────────────────────────
   Selected-tags helpers
──────────────────────────── */
function toggleOptionSelection(op) {
  const select = document.getElementById("researchAreasSelect");
  const scrollPos = select.scrollTop;
  
  op.selected = !op.selected;
  selectedResearchAreas.clear();
  Array.from(select.selectedOptions)
    .filter((o) => !o.disabled)
    .forEach((o) => selectedResearchAreas.add(o.value));

  const tagsContainer = document.getElementById("selectedTags");
  tagsContainer.innerHTML = "";

  if (!selectedResearchAreas.size) {
    tagsContainer.innerHTML = '<span class="no-tags-message">No research areas selected</span>';
    return;
  }

  selectedResearchAreas.forEach((area) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.innerHTML = `${area}<span class="remove" data-area="${area}">✕</span>`;
    tag.querySelector(".remove").addEventListener("click", () => {
      selectedResearchAreas.delete(area);
      const option = Array.from(select.options).find((o) => o.value === area);
      if (option) option.selected = false;
      toggleOptionSelection(option);
    });
    document.getElementById("selectedTags").appendChild(tag);
  });

  // Restore scroll position
  requestAnimationFrame(() => {
    select.scrollTop = scrollPos;
  });
}

/* ───────────────────────────
   Research-card rendering
──────────────────────────── */
function matchingResearchers() {
  if (!selectedResearchAreas.size) {
    return allResearchers.filter(
      (r) => researcherAreas(r).length > 0
    );
  }
  return allResearchers.filter((r) =>
    researcherAreas(r).some((a) => selectedResearchAreas.has(a))
  );
}

function displayResearchers(list) {
  const box = document.getElementById("resultsContainer");
  box.innerHTML = "";

  if (!list.length) {
    box.innerHTML = '<p class="no-results">No matching researchers found.</p>';
    return;
  }

  const unique = new Map();
  list.forEach((r) => {
    const key = r.email || r.name;
    if (!unique.has(key)) unique.set(key, r);
  });

  unique.forEach((r) => {
    const card = document.createElement("div");
    card.className = "researcher-card";

    const areas = researcherAreas(r);
    const visibleAreas = areas.slice(0, 3);
    const remainingCount = Math.max(0, areas.length - 3);

    const preview = areas.length > 0
      ? `<div class="research-areas-preview">
          ${visibleAreas.map((a) => `<span class="research-area-tag">${a}</span>`).join("")}
          ${remainingCount > 0 ? `<span class="more-tag">+${remainingCount} more</span>` : ""}
        </div>`
      : "";

    const orcidInfo = r.link?.orcid?.orcid_id
      ? `<div class="mini-orcid">
          <a href="https://orcid.org/${r.link.orcid.orcid_id}" target="_blank" title="View ORCID Profile">
            <img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" alt="ORCID" class="orcid-icon">
            <span class="orcid-id">${r.link.orcid.orcid_id}</span>
          </a>
        </div>`
      : "";

    card.innerHTML = `
      <h3>${r.name || "Unknown"}</h3>
      <p><strong>Title:</strong> ${r.title || "N/A"}</p>
      <p><strong>Email:</strong> ${r.email || "N/A"}</p>
      ${orcidInfo}
      ${preview}
    `;
    card.addEventListener("click", () => showResearcherDetails(r));
    box.appendChild(card);
  });
}

/* ───────────────────────────
   Modal helpers
──────────────────────────── */
function showResearcherDetails(r) {
  const modal = document.getElementById("modal-overlay");
  document.getElementById("modalTitle").textContent = r.name || "Details";

  const areas = researcherAreas(r);
  const body = document.getElementById("modalBody");

  let html = `<div class="researcher-info">
    <h4>Researcher Information</h4>
    <div class="info-grid">
      <div class="info-item">
        <span class="info-label">Title</span>
        <span class="info-value">${r.title || "N/A"}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Email</span>
        <span class="info-value">${r.email || "N/A"}</span>
      </div>`;

  if (r.link?.profile_link) {
    html += `<div class="info-item">
      <span class="info-label">University Profile</span>
      <span class="info-value"><a href="${r.link.profile_link}" target="_blank">View Profile</a></span>
    </div>`;
  }
  
  if (r.link?.google_scholar?.google_scholar_link) {
    html += `<div class="info-item">
      <span class="info-label">Google Scholar</span>
      <span class="info-value"><a href="${r.link.google_scholar.google_scholar_link}" target="_blank">View Publications</a></span>
    </div>`;
  }
  
  if (r.link?.personal_website) {
    html += `<div class="info-item">
      <span class="info-label">Website</span>
      <span class="info-value"><a href="${r.link.personal_website}" target="_blank">Personal Website</a></span>
    </div>`;
  }
  
  if (r.link?.orcid?.orcid_id) {
    html += `<div class="info-item">
      <span class="info-label">ORCID</span>
      <span class="info-value">
        <a href="https://orcid.org/${r.link.orcid.orcid_id}" target="_blank">
          <img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" alt="ORCID" style="height: 16px; margin-right: 4px; vertical-align: middle;">
          ${r.link.orcid.orcid_id}
        </a>
      </span>
    </div>`;
  }
  
  html += `</div></div>`;

  if (areas.length) {
    html += `<div class="research-areas-section">
      <h4>Research Areas</h4>
      <div class="research-areas-list">
        ${areas.map((a) => `<span class="research-area-tag">${a}</span>`).join("")}
      </div>
    </div>`;
  }

  body.innerHTML = html;
  modal.style.display = "flex";
  requestAnimationFrame(() => {
    modal.classList.add("active");
  });
}

function closeModal() {
  const modal = document.getElementById("modal-overlay");
  modal.classList.remove("active");
  setTimeout(() => {
    modal.style.display = "none";
  }, 300);
}

document.getElementById("modal-overlay").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) closeModal();
});

/* ───────────────────────────
   Boot‑up
──────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("topicSearch");
  let debounceTimeout;

  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      filterAndPopulateAreas(e.target.value.trim());
    }, 150);
  });

  fetch("/data/results.json")
    .then((r) => r.ok ? r.json() : Promise.reject(r.status))
    .then((data) => {
      allResearchers = data;
      rebuildTopics();
    })
    .catch((e) => {
      console.error("Loading error:", e);
      document.getElementById("resultsContainer").innerHTML = 
        '<p class="error-msg">Error loading data.</p>';
    });

  document.querySelectorAll('input[name="model"]').forEach((radio) =>
    radio.addEventListener("change", (e) => {
      currentModel = e.target.value;
      selectedResearchAreas.clear();
      rebuildTopics();
      document.getElementById("resultsContainer").innerHTML = "";
      document.getElementById("topicSearch").value = "";
    })
  );

  document.getElementById("findMatches").addEventListener("click", () => {
    const scrollPos = window.scrollY;
    displayResearchers(matchingResearchers());
    requestAnimationFrame(() => {
      window.scrollTo(0, scrollPos);
    });
  });
}); 
