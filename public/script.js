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
// let uniqueTopics = new Set(); // No longer extracting unique topics for now
let selectedTopicNames = new Set();

// Load and display research data from results.json
document.addEventListener('DOMContentLoaded', function() {
    // Set last updated time
    const now = new Date();
    document.getElementById('last-updated').textContent = now.toLocaleString();
    
    // Populate topic cards from the predefined list
    populateTopics(projectTopics);

    // Load research data (still needed for displaying researchers)
    fetch('results.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
         })
        .then(data => {
            allResearchers = data;

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
        console.log("Selected topics (ignored for now):", selectedTopicNames);
        // Display the first 5 researchers regardless of selection
        if (allResearchers.length > 0) {
             displayResearchers(allResearchers.slice(0, 5));
        } else {
             // Attempt to fetch again if data wasn't loaded initially
             fetch('results.json')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                 })
                .then(data => {
                    allResearchers = data;
                    displayResearchers(allResearchers.slice(0, 5)); 
                })
                .catch(error => {
                    console.error('Error loading research data on button click:', error);
                    document.getElementById('resultsContainer').innerHTML = '<p>Error loading research data. Please try again later.</p>';
                });
        }
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
    if (selectedTopicNames.has(topicName)) {
        selectedTopicNames.delete(topicName);
        topicCard.classList.remove('selected');
    } else {
        selectedTopicNames.add(topicName);
        topicCard.classList.add('selected');
    }
    updateSelectedTags();
}

// Function to update the display of selected tags (No changes needed here)
function updateSelectedTags() {
    const selectedTagsContainer = document.getElementById('selectedTags');
    selectedTagsContainer.innerHTML = ''; // Clear previous tags
    
    selectedTopicNames.forEach(topicName => {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.innerHTML = `
            ${topicName}
            <span class="remove" data-topic="${topicName}">✕</span>
        `;
        
        tag.querySelector('.remove').addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent card click when removing tag
            toggleTopicSelection(topicName);
        });
        
        selectedTagsContainer.appendChild(tag);
    });
}

// Function to display researchers (No changes needed here)
function displayResearchers(researchers) {
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.innerHTML = '';
    
    if (!researchers || researchers.length === 0) { // Added check for undefined/null
        // Avoid overwriting a specific fetch error message if researchers is empty due to error
        if (!resultsContainer.textContent.includes('Error')) {
             resultsContainer.innerHTML = '<p>No researchers to display.</p>';
        }
        return;
    }
    
    researchers.forEach(researcher => {
        const researcherCard = document.createElement('div');
        researcherCard.className = 'researcher-card';
        // Basic check for necessary structure
        const profileLink = researcher.link?.profile_link;
        const scholarLink = researcher.link?.google_scholar?.google_scholar_link;

        researcherCard.innerHTML = `
            <h3>${researcher.name || 'Unknown Name'}</h3>
            <p><strong>Title:</strong> ${researcher.title || 'N/A'}</p>
            <p><strong>Email:</strong> ${researcher.email || 'N/A'}</p>
            <div class="research-areas">
                ${profileLink ? `<a href="${profileLink}" target="_blank" class="research-tag">Profile</a>` : ''}
                ${scholarLink ? 
                    `<a href="${scholarLink}" target="_blank" class="research-tag">Google Scholar</a>` : ''}
            </div>
        `;
        
        // Add click event to show more details
        researcherCard.addEventListener('click', function() {
            showResearcherDetails(researcher);
        });
        
        resultsContainer.appendChild(researcherCard);
    });
}

// Function to show researcher details in modal (minor improvements for robustness)
function showResearcherDetails(researcher) {
    const modalOverlay = document.getElementById('modal-overlay');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    if (!researcher) return; // Prevent errors if researcher data is missing

    modalTitle.textContent = researcher.name || 'Details';
    
    const profileLink = researcher.link?.profile_link;
    const scholarLink = researcher.link?.google_scholar?.google_scholar_link;
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
                    <span class="info-label">Profile</span>
                    <span class="info-value"><a href="${profileLink}" target="_blank">View Profile</a></span>
                </div>` : ''}
                ${scholarLink ? 
                    `<div class="info-item">
                        <span class="info-label">Google Scholar</span>
                        <span class="info-value"><a href="${scholarLink}" target="_blank">View Profile</a></span>
                    </div>` : ''}
            </div>
        </div>
    `;
    
    // Add research areas if available
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

// Function to close modal (No changes needed here)
function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
}

// Close modal when clicking outside (No changes needed here)
document.getElementById('modal-overlay').addEventListener('click', function(event) {
    if (event.target === this) {
        closeModal();
    }
}); 