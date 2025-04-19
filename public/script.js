/* ───────────────────────────
   Global state
──────────────────────────── */
let allResearchers = [];
let uniqueResearchAreas = new Set();
let selectedResearchAreas = new Set();
let currentModel = "scraping"; // default LLM source

let selectedModel = 'all';
let selectedMatchingMethod = 'keyword';

// TF-IDF related variables
let documentVectors = {};
let idfScores = {};

function calculateTFIDF(documents) {
  // Calculate term frequencies for each document
  documentVectors = {};
  const wordCounts = {};
  
  documents.forEach((doc, docId) => {
    const words = doc.toLowerCase().split(/\W+/).filter(word => word.length > 2);
    documentVectors[docId] = {};
    
    words.forEach(word => {
      documentVectors[docId][word] = (documentVectors[docId][word] || 0) + 1;
      wordCounts[word] = (wordCounts[word] || 0) + 1;
    });
  });
  
  // Calculate IDF scores
  const totalDocs = documents.length;
  idfScores = {};
  Object.keys(wordCounts).forEach(word => {
    idfScores[word] = Math.log(totalDocs / wordCounts[word]);
  });
  
  // Calculate final TF-IDF scores
  Object.keys(documentVectors).forEach(docId => {
    const vector = documentVectors[docId];
    Object.keys(vector).forEach(word => {
      vector[word] = vector[word] * (idfScores[word] || 0);
    });
  });
}

function cosineSimilarity(vec1, vec2) {
  const intersection = Object.keys(vec1).filter(word => word in vec2);
  
  const dotProduct = intersection.reduce((sum, word) => {
    return sum + vec1[word] * vec2[word];
  }, 0);
  
  const norm1 = Math.sqrt(Object.values(vec1).reduce((sum, val) => sum + val * val, 0));
  const norm2 = Math.sqrt(Object.values(vec2).reduce((sum, val) => sum + val * val, 0));
  
  return dotProduct / (norm1 * norm2) || 0;
}

function getWordVector(text) {
  const words = text.toLowerCase().split(/\W+/).filter(word => word.length > 2);
  const vector = {};
  words.forEach(word => {
    vector[word] = (vector[word] || 0) + 1;
  });
  return vector;
}

function searchPapers() {
  const searchQuery = document.getElementById('searchInput').value.toLowerCase();
  const papers = document.querySelectorAll('.paper');
  
  if (!searchQuery) {
    papers.forEach(paper => paper.style.display = 'block');
    return;
  }
  
  let searchResults = [];
  
  papers.forEach(paper => {
    const title = paper.querySelector('h2').textContent;
    const abstract = paper.querySelector('p').textContent;
    const model = paper.getAttribute('data-model');
    
    if (selectedModel !== 'all' && model !== selectedModel) {
      paper.style.display = 'none';
      return;
    }
    
    let score = 0;
    const content = `${title} ${abstract}`.toLowerCase();
    
    switch (selectedMatchingMethod) {
      case 'keyword':
        // Simple keyword matching
        score = content.includes(searchQuery) ? 1 : 0;
        break;
        
      case 'tfidf':
        // TF-IDF similarity matching
        const queryVector = getWordVector(searchQuery);
        const docVector = documentVectors[paper.id];
        score = cosineSimilarity(queryVector, docVector);
        break;
    }
    
    searchResults.push({ paper, score });
  });
  
  // Sort and display results
  searchResults.sort((a, b) => b.score - a.score);
  searchResults.forEach(result => {
    result.paper.style.display = result.score > 0 ? 'block' : 'none';
  });
}

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
    .filter(area => !searchQuery || area.toLowerCase().includes(searchQuery.toLowerCase()))
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

  sel.addEventListener("keydown", (e) => {
    if (e.code === "Space") {
      e.preventDefault();
      toggleOptionSelection(sel.options[sel.selectedIndex]);
    }
  });
  
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
  updateSelectedTags();
}

/* ───────────────────────────
   Selected‑tags helpers
──────────────────────────── */
function toggleOptionSelection(op) {
  const select = document.getElementById("researchAreasSelect");
  const scrollPos = select.scrollTop;
  
  op.selected = !op.selected;
  selectedResearchAreas.clear();
  Array.from(select.selectedOptions)
    .filter((o) => !o.disabled)
    .forEach((o) => selectedResearchAreas.add(o.value));

  // Just update the tags without rebuilding the dropdown
  updateSelectedTags();
  
  // Restore scroll position
  select.scrollTop = scrollPos;
}

function updateSelectedTags() {
  const wrap = document.getElementById("selectedTags");
  wrap.innerHTML = "";

  if (!selectedResearchAreas.size) {
    wrap.innerHTML =
      '<span class="no-tags-message">No research areas selected</span>';
    return;
  }

  selectedResearchAreas.forEach((area) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.innerHTML = `${area}<span class="remove" data-area="${area}">✕</span>`;
    tag.querySelector(".remove").addEventListener("click", () => {
      selectedResearchAreas.delete(area);
      const op = document.querySelector(
        `#researchAreasSelect option[value="${area}"]`
      );
      if (op) op.selected = false;
      updateSelectedTags();
    });
    wrap.appendChild(tag);
  });
}

/* ───────────────────────────
   Research‑card rendering
──────────────────────────── */
function matchingResearchers() {
  if (!selectedResearchAreas.size) {
    // No filter chosen → show everyone with at least one area for this model
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
    box.innerHTML =
      '<p class="no-results">No matching researchers found.</p>';
    return;
  }

  const unique = new Map(); // dedupe by email when available
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
          ${visibleAreas.map(a => `<span class="research-area-tag">${a}</span>`).join("")}
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

  if (r.link?.profile_link)
    html += `<div class="info-item">
      <span class="info-label">University Profile</span>
      <span class="info-value"><a href="${r.link.profile_link}" target="_blank">View Profile</a></span>
    </div>`;
  if (r.link?.google_scholar?.google_scholar_link)
    html += `<div class="info-item">
      <span class="info-label">Google Scholar</span>
      <span class="info-value"><a href="${r.link.google_scholar.google_scholar_link}" target="_blank">View Publications</a></span>
    </div>`;
  if (r.link?.personal_website)
    html += `<div class="info-item">
      <span class="info-label">Website</span>
      <span class="info-value"><a href="${r.link.personal_website}" target="_blank">Personal Website</a></span>
    </div>`;
  if (r.link?.orcid?.orcid_id)
    html += `<div class="info-item">
      <span class="info-label">ORCID</span>
      <span class="info-value">
        <a href="https://orcid.org/${r.link.orcid.orcid_id}" target="_blank">
          <img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" alt="ORCID" style="height: 16px; margin-right: 4px; vertical-align: middle;">
          ${r.link.orcid.orcid_id}
        </a>
      </span>
    </div>`;
  html += "</div></div>";

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
  // Trigger animation
  requestAnimationFrame(() => {
    modal.classList.add("active");
  });
}

function closeModal() {
  const modal = document.getElementById("modal-overlay");
  modal.classList.remove("active");
  // Wait for animation to complete before hiding
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
  // Add search input handler
  const searchInput = document.getElementById("topicSearch");
  let debounceTimeout;

  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      filterAndPopulateAreas(e.target.value.trim());
    }, 150); // Debounce for better performance
  });

  // Fetch faculty JSON but don't display initially
  fetch("/data/results.json")
    .then((r) => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    })
    .then((data) => {
      allResearchers = data;
      rebuildTopics();
    })
    .catch((e) => {
      console.error("Loading error:", e);
      document.getElementById(
        "resultsContainer"
      ).innerHTML = `<p class="error-msg">Error loading data.</p>`;
    });

  /* radio‑button change */
  document
    .querySelectorAll('input[name="model"]')
    .forEach((radio) =>
      radio.addEventListener("change", (e) => {
        currentModel = e.target.value;
        selectedResearchAreas.clear();
        rebuildTopics();
        // Clear results when model changes
        document.getElementById("resultsContainer").innerHTML = "";
        // Clear search
        document.getElementById("topicSearch").value = "";
      })
    );

  /* Find Matches button */
  document
    .getElementById("findMatches")
    .addEventListener("click", () => {
      // Store current scroll position
      const scrollPos = window.scrollY;
      
      // Display results
      displayResearchers(matchingResearchers());
      
      // Restore scroll position after a brief delay to ensure DOM updates
      requestAnimationFrame(() => {
        window.scrollTo(0, scrollPos);
      });
    });

  // Initialize matching method selection
  document.querySelectorAll('input[name="matching-method"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      selectedMatchingMethod = e.target.value;
      searchPapers();
    });
  });

  // Initialize TF-IDF when the page loads
  window.addEventListener('load', () => {
    // Calculate TF-IDF for all papers
    const papers = document.querySelectorAll('.paper');
    const documents = Array.from(papers).map(paper => {
      const title = paper.querySelector('h2').textContent;
      const abstract = paper.querySelector('p').textContent;
      return `${title} ${abstract}`;
    });
    
    calculateTFIDF(documents);
  });
});