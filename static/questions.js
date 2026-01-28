document.addEventListener("DOMContentLoaded", () => {
    // 1. Extract Concept ID from URL
    const urlParts = window.location.pathname.split('/');
    const conceptId = urlParts[urlParts.length - 1];

    // 2. Fetch Questions from API
    fetch(`/api/get_questions/${conceptId}`)
        .then(res => res.json())
        .then(questions => {
            const tableBody = document.getElementById("questions-table-body");
            if (!tableBody) return;
            console.log("HII")
            tableBody.innerHTML = ""; // Clear loading state

            questions.forEach(q => {
                const row = document.createElement("tr");
                row.className = "align-middle mb-2";

                // New Row HTML: Replaced 'Mark Done' with 'Solve Problem'
                row.innerHTML = `
                    <td class="ps-4" style="width: 60px;">
                        ${q.is_solved 
                            ? '<div class="bg-success-subtle p-2 rounded-circle text-center" style="width:35px; height:35px;"><i class="bi bi-check2 text-success fw-bold"></i></div>' 
                            : '<div class="bg-light p-2 rounded-circle text-center" style="width:35px; height:35px;"><i class="bi bi-circle text-secondary"></i></div>'}
                    </td>
                    <td>
                        <div class="fw-bold text-dark mb-0">${q.title}</div>
                        <a href="${q.link}" target="_blank" class="text-primary x-small text-decoration-none" style="font-size: 0.75rem;">
                            View on LeetCode <i class="bi bi-box-arrow-up-right"></i>
                        </a>
                    </td>
                    <td>
                        <span class="badge badge-premium rounded-pill ${getBadgeClass(q.difficulty)}">
                            ${q.difficulty}
                        </span>
                    </td>
                    <td class="text-end pe-4">
                        <button class="btn btn-sm btn-dark rounded-pill px-4 fw-medium" 
                                onclick="openWorkstation(${q.id})">
                            Solve Problem <i class="bi bi-arrow-right-short"></i>
                        </button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(err => console.error("Error fetching questions:", err));
});

// --- WORKSTATION MODAL LOGIC ---

let currentQuestionId = null; // Global variable to track which question is open

async function openWorkstation(questionId) {
    currentQuestionId = questionId;
    
    // 1. Show the Modal immediately (shows "Loading..." initially)
    const modalElement = document.getElementById('workstationModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();

    // Reset UI to "Loading" state while fetching
    document.getElementById("ws-title").innerText = "Loading...";
    document.getElementById("ws-description").innerText = "Fetching problem details...";
    document.getElementById("ws-chat-box").innerHTML = '<div class="text-center text-muted mt-5"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Loading AI Context...</div>';

    try {
        // 2. Fetch Question Details from Backend
        const response = await fetch(`/api/get_question_details/${questionId}`);
        const data = await response.json();

        // 3. Update the Modal Content
        document.getElementById("ws-title").innerText = data.title;
        document.getElementById("ws-description").innerText = data.description || "No description available for this problem.";

        // 4. Update the 'Mark Done' Button inside the modal
        updateWorkstationButton(data.is_solved);

        // 5. Initialize the Chat
        document.getElementById("ws-chat-box").innerHTML = `
            <div class="alert alert-light border small">
                I'm ready to help with <b>"${data.title}"</b>. You can ask for hints, approach explanation, or time complexity analysis!
            </div>`;

    } catch (err) {
        console.error("Error loading workstation:", err);
        document.getElementById("ws-description").innerText = "Error loading problem details.";
    }
}

// Helper to update the button inside the modal
function updateWorkstationButton(isSolved) {
    const btn = document.getElementById("ws-mark-done-btn");
    
    if (isSolved) {
        btn.className = "btn btn-lg btn-outline-secondary w-100 rounded-3";
        btn.innerHTML = '<i class="bi bi-arrow-counterclockwise me-2"></i> Reset Progress';
        // When clicking Reset, call toggleSolve
        btn.onclick = () => handleWorkstationToggle(); 
    } else {
        btn.className = "btn btn-lg btn-success w-100 rounded-3";
        btn.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i> Mark Problem as Solved';
        // When clicking Mark Done, call toggleSolve
        btn.onclick = () => handleWorkstationToggle();
    }
}

// Function to handle the actual API call when clicking the big button
function handleWorkstationToggle() {
    if (!currentQuestionId) return;

    fetch('/api/toggle_solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: currentQuestionId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            // Update the button state dynamically without reloading
            const isNowSolved = (data.action === 'solved');
            updateWorkstationButton(isNowSolved);
            
            // Optional: Refresh the background table row if you want, 
            // or just reload the page when the modal closes.
        } else {
            alert("Error updating status: " + data.error);
        }
    })
    .catch(err => console.error("Error toggling solve:", err));
}

// Helper function for badges
function getBadgeClass(diff) {
    if (diff === 'Easy') return 'bg-success-subtle text-success border border-success';
    if (diff === 'Medium') return 'bg-warning-subtle text-warning-emphasis border border-warning';
    if (diff === 'Hard') return 'bg-danger-subtle text-danger border border-danger';
    return 'bg-secondary-subtle';
}
// Add this to questions.js

function askAI() {
    const inputField = document.getElementById("ws-user-input");
    const chatBox = document.getElementById("ws-chat-box");
    const userText = inputField.value.trim();
    
    if (!userText || !currentQuestionId) return;

    // 1. Add User Message to Chat
    chatBox.innerHTML += `
        <div class="d-flex justify-content-end mb-3">
            <div class="bg-primary text-white p-3 rounded-3" style="max-width: 80%;">
                ${userText}
            </div>
        </div>`;
    
    inputField.value = ""; // Clear input
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll down

    // 2. Add "Thinking..." bubble
    const loadingId = "loading-" + Date.now();
    chatBox.innerHTML += `
        <div id="${loadingId}" class="d-flex justify-content-start mb-3">
            <div class="bg-light border p-3 rounded-3 text-muted small">
                <div class="spinner-border spinner-border-sm me-2"></div> Thinking...
            </div>
        </div>`;

    // 3. Send to your Backend (Where your LangGraph will live)
    fetch('/api/ask_ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            question_id: currentQuestionId, 
            query: userText 
        })
    })
    .then(res => res.json())
    .then(data => {
        // Remove loading bubble
        document.getElementById(loadingId).remove();
        
        // Add AI Response
        chatBox.innerHTML += `
            <div class="d-flex justify-content-start mb-3">
                <div class="bg-white border p-3 rounded-3 shadow-sm" style="max-width: 85%;">
                    <i class="bi bi-robot text-primary me-2"></i>
                    ${data.answer}
                </div>
            </div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(err => {
        document.getElementById(loadingId).innerHTML = '<span class="text-danger">Error reaching AI agent.</span>';
    });
}

// Optional: Allow "Enter" key to send
document.getElementById("ws-user-input").addEventListener("keypress", function(event) {
    if (event.key === "Enter") askAI();
});