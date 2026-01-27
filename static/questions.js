document.addEventListener("DOMContentLoaded", () => {
    // 1. Extract ID from URL
    const urlParts = window.location.pathname.split('/');
    const conceptId = urlParts[urlParts.length - 1];
    
    // 2. Fetch data from your Flask API
    fetch(`/api/get_questions/${conceptId}`)
        .then(res => res.json())
        .then(questions => {
            const tableBody = document.getElementById("questions-table-body");
            if (!tableBody) return; // Safety check
            
            tableBody.innerHTML = ""; // Clear "Loading..."

            questions.forEach(q => {
                // IMPORTANT: You must create the table row element (tr) first!
                const row = document.createElement("tr");
                row.className = "align-middle mb-2"; // Premium vertical alignment

                // Now we fill that specific row with your "Classy" design
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
                        <button class="btn btn-sm ${q.is_solved ? 'btn-light text-muted' : 'btn-dark'} rounded-pill px-4 fw-medium" 
                                onclick="toggleSolve(${q.id}, ${q.is_solved})">
                            ${q.is_solved ? 'Reset' : 'Mark Done'}
                        </button>
                    </td>
                `;

                // FINALLY: Add the finished row to the table body
                tableBody.appendChild(row);
            });
        })
        .catch(err => console.error("Error fetching questions:", err));
});

// Helper function to handle the premium badge colors
function getBadgeClass(diff) {
    if (diff === 'Easy') return 'bg-success-subtle text-success border border-success';
    if (diff === 'Medium') return 'bg-warning-subtle text-warning-emphasis border border-warning';
    if (diff === 'Hard') return 'bg-danger-subtle text-danger border border-danger';
    return 'bg-secondary-subtle';
}