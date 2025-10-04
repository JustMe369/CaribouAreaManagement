// Initialize charts when the page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    setupEventListeners();
});

function initializeCharts() {
    // Trend Chart (Last 30 days)
    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        const trendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: ['Jan 1', 'Jan 5', 'Jan 10', 'Jan 15', 'Jan 20', 'Jan 25', 'Jan 30'],
                datasets: [
                    {
                        label: 'New Tickets',
                        data: [5, 8, 6, 10, 7, 12, 9],
                        borderColor: 'rgba(139, 69, 19, 1)',
                        backgroundColor: 'rgba(139, 69, 19, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Resolved Tickets',
                        data: [3, 5, 7, 6, 9, 8, 11],
                        borderColor: 'rgba(40, 167, 69, 1)',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Tickets'
                        }
                    }
                }
            }
        });
    }

    // Status Distribution Chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        const statusChart = new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'In Progress', 'Completed', 'Overdue'],
                datasets: [{
                    data: [stats.pending, stats.in_progress, stats.completed, stats.overdue],
                    backgroundColor: [
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(23, 162, 184, 0.8)',
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(220, 53, 69, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }
}

function setupEventListeners() {
    // Create ticket button
    const createBtn = document.getElementById('createTicketBtn');
    if (createBtn) {
        createBtn.addEventListener('click', function() {
            const visitSelector = document.getElementById('visitSelector');
            const visitId = visitSelector.value;
            if (visitId && visitId !== 'Choose a visit...') {
                let url = newMaintenanceUrl.replace('0', visitId);
                window.location.href = url;
            } else {
                alert('Please select a visit first.');
            }
        });
    }
    
    // Ticket view modal
    const viewButtons = document.querySelectorAll('.view-ticket');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const ticketId = this.getAttribute('data-ticket-id');
            loadTicketDetails(ticketId);
        });
    });
    
    // Delete ticket buttons
    const deleteButtons = document.querySelectorAll('.delete-ticket');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const ticketId = this.getAttribute('data-ticket-id');
            showDeleteConfirmation(ticketId);
        });
    });
    
    // Confirm delete button
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            const ticketId = document.getElementById('deleteTicketId').textContent;
            deleteTicket(ticketId);
        });
    }

    // Search functionality
    const searchBox = document.querySelector('.search-box input');
    if (searchBox) {
        searchBox.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

function loadTicketDetails(ticketId) {
    // Show loading state
    document.getElementById('ticketDetailContent').innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading ticket details...</p>
        </div>
    `;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('ticketDetailModal'));
    modal.show();
    
    // In a real application, you would fetch this data from the server
    // For this example, we'll simulate a delay and then show mock data
    setTimeout(() => {
        document.getElementById('ticketDetailContent').innerHTML = `
            <div class="ticket-details">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <strong>Ticket ID:</strong> #${ticketId}
                    </div>
                    <div class="col-md-6">
                        <strong>Status:</strong> <span class="badge bg-warning">Pending</span>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-6">
                        <strong>Store:</strong> Downtown Location
                    </div>
                    <div class="col-md-6">
                        <strong>Priority:</strong> <span class="badge bg-danger">High</span>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-6">
                        <strong>Issue Type:</strong> Equipment Repair
                    </div>
                    <div class="col-md-6">
                        <strong>Reported By:</strong> John Smith
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-6">
                        <strong>Created:</strong> Jan 15, 2023
                    </div>
                    <div class="col-md-6">
                        <strong>Due Date:</strong> Jan 22, 2023
                    </div>
                </div>
                <div class="mb-3">
                    <strong>Description:</strong>
                    <p>The espresso machine is leaking water and producing inconsistent shots. Needs urgent repair.</p>
                </div>
                <div class="mb-3">
                    <strong>Technician Notes:</strong>
                    <p>Diagnosed issue with water pump. Parts have been ordered and will arrive tomorrow.</p>
                </div>
                <div class="mb-3">
                    <strong>Attachments:</strong>
                    <ul class="list-group">
                        <li class="list-group-item">
                            <i class="fas fa-file-image"></i> machine_damage.jpg
                            <a href="#" class="btn btn-sm btn-outline-primary float-end">View</a>
                        </li>
                        <li class="list-group-item">
                            <i class="fas fa-file-pdf"></i> service_manual.pdf
                            <a href="#" class="btn btn-sm btn-outline-primary float-end">Download</a>
                        </li>
                    </ul>
                </div>
            </div>
        `;
        
        // Update edit button link
        document.getElementById('editTicketBtn').href = `/maintenance/${ticketId}/edit/`;
    }, 800);
}

function showDeleteConfirmation(ticketId) {
    document.getElementById('deleteTicketId').textContent = ticketId;
    const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    modal.show();
}

function deleteTicket(ticketId) {
    // In a real application, you would send a DELETE request to the server
    // For this example, we'll simulate deletion
    console.log(`Deleting ticket #${ticketId}`);
    
    // Close the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
    modal.hide();
    
    // Show success message
    alert(`Ticket #${ticketId} has been deleted successfully.`);
    
    // In a real app, you would refresh the page or remove the row from the table
    // For now, we'll just reload the page
    location.reload();
}