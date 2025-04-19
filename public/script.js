// Predefined project topics for now
const projectTopics = [
    "High Performance Computing",
    "Data Analytics",
    "Bioinformatics",
    "Systems Biology",
    "Combinatorial Scientific Computing",
    "Applied Algorithms",
    "Data Science",
    "Computational Biology",
    "Machine Learning",
    "Artificial Intelligence",
    "Cybersecurity",
    "Human-Computer Interaction"
];

// Global array to hold all researcher data
let allResearchers = [];
// Set to hold unique research areas
let uniqueResearchAreas = new Set();
// Set to hold selected research areas
let selectedResearchAreas = new Set();

// Function to clean up research area text
function cleanResearchArea(area) {
    // Common abbreviations and their full forms
    const abbreviations = {
        'ai': 'Artificial Intelligence',
        'ml': 'Machine Learning',
        'nlp': 'Natural Language Processing',
        'hci': 'Human Computer Interaction',
        'iot': 'Internet of Things',
        'ar': 'Augmented Reality',
        'vr': 'Virtual Reality',
        'xr': 'Extended Reality',
        'os': 'Operating Systems',
        'db': 'Database',
        'ui': 'User Interface',
        'ux': 'User Experience'
    };

    // Words that should remain lowercase
    const lowercaseWords = new Set(['a', 'an', 'the', 'and', 'or', 'but', 'nor', 'for', 'yet', 'so', 'at', 'by', 'for', 'in', 'of', 'on', 'to', 'up', 'as']);

    return area
        .toLowerCase()
        .trim()
        // Replace special characters with spaces
        .replace(/[&\/\\#,+()$~%.'":*?<>{}]/g, ' ')
        // Replace multiple spaces with single space
        .replace(/\s+/g, ' ')
        // Split into words
        .split(' ')
        // Process each word
        .map(word => {
            // Check if it's a known abbreviation
            if (abbreviations[word]) {
                return abbreviations[word];
            }
            // If it's a word that should be lowercase, return it as is
            if (lowercaseWords.has(word)) {
                return word;
            }
            // Otherwise capitalize first letter
            return word.charAt(0).toUpperCase() + word.slice(1);
        })
        .join(' ')
        // Clean up any remaining issues
        .trim()
        // Remove standalone conjunctions at the start
        .replace(/^(and|or|&)\s+/i, '')
        // Remove standalone conjunctions at the end
        .replace(/\s+(and|or|&)$/i, '')
        // Replace ' And ' with ' and '
        .replace(/\s+And\s+/g, ' and ')
        // Replace ' Or ' with ' or '
        .replace(/\s+Or\s+/g, ' or ');
}

// Load and display research data from results.json
document.addEventListener('DOMContentLoaded', function() {
    // Set last updated time
    const now = new Date();
    document.getElementById('last-updated').textContent = now.toLocaleString();
    
    // Populate topic cards from the predefined list
    populateTopics(projectTopics);

    // Load research data
    fetch('../results.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
         })
        .then(data => {
            allResearchers = data;
            // Extract unique research areas with cleaned text
            const seenAreas = new Set(); // Track cleaned areas to avoid duplicates
            data.forEach(researcher => {
                if (researcher.research_areas && Array.isArray(researcher.research_areas)) {
                    researcher.research_areas.forEach(area => {
                        if (area) {
                            const cleanedArea = cleanResearchArea(area);
                            if (!seenAreas.has(cleanedArea)) {
                                seenAreas.add(cleanedArea);
                                uniqueResearchAreas.add(cleanedArea);
                            }
                        }
                    });
                }
            });
            // Populate research areas dropdown
            populateResearchAreasDropdown();
        })
        .catch(error => {
            console.error('Error loading research data:', error);
            // Display error message for data loading, but topics should still load
            document.getElementById('resultsContainer').innerHTML = '<p>Error loading research data. Please try again later.</p>';
            // Clear topics container error if it was previously set
            const topicsContainer = document.getElementById('topicsContainer');
            if (topicsContainer.textContent.includes("Error")) { // Basic check
                 // If topics were populated successfully, we don't need an error here
            } else if (topicsContainer.innerHTML === '') {
                 topicsContainer.innerHTML = '<p>Loading topics...</p>'; // Or handle differently
            }
        });
    
    // Set up event listeners
    document.getElementById('findMatches').addEventListener('click', function() {
        const selectedAreas = Array.from(selectedResearchAreas);
        
        const matchingResearchers = allResearchers.filter(researcher => {
            if (!researcher.research_areas || !Array.isArray(researcher.research_areas)) return false;
            return researcher.research_areas.some(area => 
                selectedAreas.includes(cleanResearchArea(area))
            );
        });
        
        displayResearchers(matchingResearchers);
    });
});

// Function to populate topic cards (Uses the predefined list now)
function populateTopics(topics) {
    const topicsContainer = document.getElementById('topicsContainer');
    topicsContainer.innerHTML = ''; // Clear previous content (like error messages)
    topics.sort(); // Sort topics alphabetically

    topics.forEach(topic => {
        if (!topic) return; // Skip null or empty topics
        
        const topicCard = document.createElement('div');
        topicCard.className = 'topic-card';
        topicCard.dataset.topic = topic; // Store topic name in data attribute
        topicCard.innerHTML = `<h4>${topic}</h4>`; // Display topic name
        
        topicCard.addEventListener('click', () => toggleTopicSelection(topic));
        topicsContainer.appendChild(topicCard);
    });
}

// Function to handle topic selection/deselection (No changes needed here)
function toggleTopicSelection(topicName) {
    const topicCard = document.querySelector(`.topic-card[data-topic="${topicName}"]`);
    if (!topicCard) return; // Add guard clause
    if (selectedResearchAreas.has(topicName)) {
        selectedResearchAreas.delete(topicName);
        topicCard.classList.remove('selected');
    } else {
        selectedResearchAreas.add(topicName);
        topicCard.classList.add('selected');
    }
    updateSelectedTags();
}

// Function to populate research areas dropdown
function populateResearchAreasDropdown() {
    const topicsContainer = document.getElementById('topicsContainer');
    topicsContainer.innerHTML = ''; // Clear previous content
    
    // Create a select element
    const select = document.createElement('select');
    select.id = 'researchAreasSelect';
    select.multiple = true;
    select.size = 15;

    // Create and add a helper text option that can't be selected
    const helperOption = document.createElement('option');
    helperOption.disabled = true;
    helperOption.textContent = '↑↓ to navigate, space to select, or click';
    select.appendChild(helperOption);
    
    // Add options for each research area
    Array.from(uniqueResearchAreas).sort().forEach(area => {
        const option = document.createElement('option');
        option.value = area;
        option.textContent = area;
        select.appendChild(option);
    });
    
    // Handle keyboard navigation and selection
    select.addEventListener('keydown', function(e) {
        if (e.code === 'Space') {
            e.preventDefault();
            const scrollTop = this.scrollTop; // Store scroll position
            const option = this.options[this.selectedIndex];
            if (option && !option.disabled) {
                toggleOptionSelection(option);
                // Restore scroll position after a brief delay
                setTimeout(() => {
                    this.scrollTop = scrollTop;
                }, 0);
            }
        }
    });

    // Handle mouse selection
    select.addEventListener('mousedown', function(e) {
        e.preventDefault();
        const scrollTop = this.scrollTop; // Store scroll position
        
        const option = e.target.closest('option');
        if (!option || option.disabled) return;
        
        toggleOptionSelection(option);
        
        // Restore scroll position after a brief delay
        setTimeout(() => {
            this.scrollTop = scrollTop;
        }, 0);
    });
    
    // Prevent scroll reset on focus
    select.addEventListener('focus', function(e) {
        const scrollTop = this.scrollTop;
        setTimeout(() => {
            this.scrollTop = scrollTop;
        }, 0);
    });
    
    topicsContainer.appendChild(select);
    
    // Initial update of selected tags
    updateSelectedTags();
}

// Function to toggle option selection with visual feedback
function toggleOptionSelection(option) {
    const select = document.getElementById('researchAreasSelect');
    
    // Toggle selection
    option.selected = !option.selected;
    
    // Update selected areas
    selectedResearchAreas.clear();
    Array.from(select.selectedOptions).forEach(opt => {
        if (!opt.disabled) {
            selectedResearchAreas.add(opt.value);
        }
    });
    
    // Add brief highlight effect
    const originalBackground = option.style.backgroundColor;
    option.style.backgroundColor = 'var(--bg-card-hover)';
    setTimeout(() => {
        option.style.backgroundColor = originalBackground;
    }, 150);
    
    updateSelectedTags();
}

// Function to update the display of selected tags
function updateSelectedTags() {
    const selectedTagsContainer = document.getElementById('selectedTags');
    selectedTagsContainer.innerHTML = '';
    
    if (selectedResearchAreas.size === 0) {
        selectedTagsContainer.innerHTML = '<span class="no-tags-message">No research areas selected</span>';
        return;
    }
    
    selectedResearchAreas.forEach(area => {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.innerHTML = `
            ${area}
            <span class="remove" data-area="${area}">✕</span>
        `;
        
        tag.querySelector('.remove').addEventListener('click', (e) => {
            e.stopPropagation();
            
            // Remove from selected areas
            selectedResearchAreas.delete(area);
            
            // Deselect in dropdown
            const option = document.querySelector(`#researchAreasSelect option[value="${area}"]`);
            if (option) {
                option.selected = false;
                // Add brief highlight effect
                option.style.backgroundColor = 'var(--bg-card-hover)';
                setTimeout(() => {
                    option.style.backgroundColor = '';
                }, 150);
            }
            
            updateSelectedTags();
        });
        
        selectedTagsContainer.appendChild(tag);
    });
}

// Function to display researchers with deduplication
function displayResearchers(researchers) {
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.innerHTML = '';
    
    if (!researchers || researchers.length === 0) {
        resultsContainer.innerHTML = '<p class="no-results">No matching researchers found.</p>';
        return;
    }
    
    // Deduplicate researchers based on email
    const uniqueResearchers = new Map();
    researchers.forEach(researcher => {
        if (researcher.email && !uniqueResearchers.has(researcher.email)) {
            uniqueResearchers.set(researcher.email, researcher);
        }
    });
    
    // Convert Map values back to array and create cards
    Array.from(uniqueResearchers.values()).forEach(researcher => {
        const researcherCard = document.createElement('div');
        researcherCard.className = 'researcher-card';
        
        // Create research areas tags HTML if available
        const researchAreasHTML = researcher.research_areas && Array.isArray(researcher.research_areas) && researcher.research_areas.length > 0
            ? `<div class="research-areas-preview">
                ${researcher.research_areas.slice(0, 3).map(area => 
                    `<span class="research-area-tag">${area}</span>`
                ).join('')}
                ${researcher.research_areas.length > 3 ? 
                    `<span class="research-area-tag">+${researcher.research_areas.length - 3} more</span>` : 
                    ''}
               </div>`
            : '';
        
        researcherCard.innerHTML = `
            <h3>${researcher.name || 'Unknown Name'}</h3>
            <p><strong>Title:</strong> ${researcher.title || 'N/A'}</p>
            <p><strong>Email:</strong> ${researcher.email || 'N/A'}</p>
            ${researchAreasHTML}
            <div class="researcher-links">
                ${researcher.link?.profile_link ? 
                    `<a href="${researcher.link.profile_link}" target="_blank" class="research-tag">Profile</a>` : ''}
                ${researcher.link?.google_scholar?.google_scholar_link ? 
                    `<a href="${researcher.link.google_scholar.google_scholar_link}" target="_blank" class="research-tag">Google Scholar</a>` : ''}
                ${researcher.link?.personal_website ? 
                    `<a href="${researcher.link.personal_website}" target="_blank" class="research-tag">Website</a>` : ''}
                ${researcher.link?.orcid?.orcid_id ? 
                    `<a href="${researcher.link.orcid.orcid_link}" target="_blank" class="research-tag">ORCID</a>` : ''}
            </div>
        `;
        
        researcherCard.addEventListener('click', function() {
            showResearcherDetails(researcher);
        });
        
        resultsContainer.appendChild(researcherCard);
    });
}

// Function to show researcher details in modal
function showResearcherDetails(researcher) {
    const modalOverlay = document.getElementById('modal-overlay');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = researcher.name || 'Details';
    
    const profileLink = researcher.link?.profile_link;
    const scholarLink = researcher.link?.google_scholar?.google_scholar_link;
    const personalWebsite = researcher.link?.personal_website;
    const orcidId = researcher.link?.orcid?.orcid_id;
    const orcidLink = researcher.link?.orcid?.orcid_link;
    const researchAreas = researcher.research_areas;

    let modalContent = `
        <div class="researcher-info">
            <h4>Researcher Information</h4>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Title</span>
                    <span class="info-value">${researcher.title || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Email</span>
                    <span class="info-value">${researcher.email || 'N/A'}</span>
                </div>
                ${profileLink ? 
                    `<div class="info-item">
                        <span class="info-label">University Profile</span>
                        <span class="info-value"><a href="${profileLink}" target="_blank">View Profile</a></span>
                    </div>` : ''}
                ${scholarLink ? 
                    `<div class="info-item">
                        <span class="info-label">Google Scholar</span>
                        <span class="info-value"><a href="${scholarLink}" target="_blank">View Profile</a></span>
                    </div>` : ''}
                ${personalWebsite ? 
                    `<div class="info-item">
                        <span class="info-label">Personal Website</span>
                        <span class="info-value"><a href="${personalWebsite}" target="_blank">Visit Website</a></span>
                    </div>` : ''}
                ${orcidId ? 
                    `<div class="info-item">
                        <span class="info-label">ORCID ID</span>
                        <span class="info-value"><a href="${orcidLink}" target="_blank">${orcidId}</a></span>
                    </div>` : ''}
            </div>
        </div>
    `;
    
    if (researchAreas && Array.isArray(researchAreas) && researchAreas.length > 0) {
        modalContent += `
            <div class="research-areas-section">
                <h4>Research Areas</h4>
                <div class="research-areas-list">
                    ${researchAreas.filter(area => area).map(area => `<span class="research-area-tag">${area}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    modalBody.innerHTML = modalContent;
    modalOverlay.style.display = 'flex';
}

// Function to close modal
function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
}

// Close modal when clicking outside
document.getElementById('modal-overlay').addEventListener('click', function(event) {
    if (event.target === this) {
        closeModal();
    }
});