// Enhanced Maintenance List JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    setupEventListeners();
    animateStats();
});

function initializeCharts() {
    setupTrendChart();
    setupStatusChart();
}

function setupTrendChart() {
    const ctx = document.getElementById('trendChart');
    if (!ctx) return;

    // eslint-disable-next-line no-new
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'New Tickets',
                data: [12, 19, 15, 25, 22, 18],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6
            }, {
                label: 'Resolved',
                data: [8, 15, 12, 20, 18, 16],
                borderColor: '#38ef7d',
                backgroundColor: 'rgba(56, 239, 125, 0.1)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#38ef7d',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function setupStatusChart() {
    const ctx = document.getElementById('statusChart');
    if (!ctx) return;

    const pending = parseInt(document.querySelector('.stat-card .stat-number').textContent) || 0;
    const inProgress = parseInt(document.querySelectorAll('.stat-card .stat-number')[2]?.textContent) || 0;
    const completed = parseInt(document.querySelectorAll('.stat-card .stat-number')[3]?.textContent) || 0;
    const overdue = parseInt(document.querySelectorAll('.stat-card .stat-number')[4]?.textContent) || 0;

    // eslint-disable-next-line no-new
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Pending', 'In Progress', 'Completed', 'Overdue'],
            datasets: [{
                data: [pending, inProgress, completed, overdue],
                backgroundColor: [
                    '#f093fb',
                    '#4facfe',
                    '#38ef7d',
                    '#fc466b'
                ],
                borderWidth: 0,
                cutout: '60%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                }
            }
        }
    });
}

function setupEventListeners() {
    // Create ticket button
    const createTicketBtn = document.getElementById('createTicketBtn');
    if (createTicketBtn) {
        createTicketBtn.addEventListener('click', function() {
            const visitSelector = document.getElementById('visitSelector');
            const visitId = visitSelector ? visitSelector.value : null;
            
            if (visitId && visitId !== 'Choose a visit...') {
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Creating...';
                this.disabled = true;
                window.location.href = `/checklist/maintenance/new/${visitId}/`;
            } else {
                alert('Please select a visit from the dropdown first.');
            }
        });
    }

    // View ticket buttons
    document.querySelectorAll('.btn-view').forEach(btn => {
        btn.addEventListener('click', function() {
            const ticketId = this.dataset.ticketId;
            showTicketDetails(ticketId);
        });
    });

    // Delete ticket buttons
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const ticketId = this.dataset.ticketId;
            if (confirm('Are you sure you want to delete this ticket?')) {
                deleteTicket(ticketId);
            }
        });
    });

    // Search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterTickets(this.value);
            }, 300);
        });
    }

    // Floating action button animation
    const floatingBtn = document.querySelector('.floating-action');
    if (floatingBtn) {
        floatingBtn.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1) rotate(90deg)';
        });
        floatingBtn.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
        });
    }
}

function animateStats() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    statNumbers.forEach(stat => {
        const finalValue = parseInt(stat.textContent);
        let currentValue = 0;
        const increment = finalValue / 50;
        
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                stat.textContent = finalValue;
                clearInterval(timer);
            } else {
                stat.textContent = Math.floor(currentValue);
            }
        }, 30);
    });
}

function showTicketDetails(ticketId) {
    // Create and show modal with ticket details
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Ticket #${ticketId} Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2">Loading ticket details...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Simulate loading ticket details
    setTimeout(() => {
        modal.querySelector('.modal-body').innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Ticket Information</h6>
                    <p><strong>ID:</strong> #${ticketId}</p>
                    <p><strong>Status:</strong> <span class="badge bg-warning">Pending</span></p>
                    <p><strong>Priority:</strong> <span class="badge bg-danger">High</span></p>
                    <p><strong>Store:</strong> Downtown Location</p>
                </div>
                <div class="col-md-6">
                    <h6>Timeline</h6>
                    <p><strong>Created:</strong> ${new Date().toLocaleDateString()}</p>
                    <p><strong>Due Date:</strong> ${new Date(Date.now() + 7*24*60*60*1000).toLocaleDateString()}</p>
                    <p><strong>Last Updated:</strong> ${new Date().toLocaleDateString()}</p>
                </div>
            </div>
            <div class="mt-3">
                <h6>Description</h6>
                <p>Equipment maintenance required for optimal performance. Issue reported by store manager.</p>
            </div>
        `;
    }, 1000);
    
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
}

function deleteTicket(ticketId) {
    // Simulate ticket deletion
    const ticketCard = document.querySelector(`[data-ticket-id="${ticketId}"]`).closest('.ticket-card');
    
    if (ticketCard) {
        ticketCard.style.transition = 'all 0.3s ease';
        ticketCard.style.transform = 'scale(0)';
        ticketCard.style.opacity = '0';
        
        setTimeout(() => {
            ticketCard.remove();
            showNotification('Ticket deleted successfully', 'success');
        }, 300);
    }
}

function filterTickets(searchTerm) {
    const tickets = document.querySelectorAll('.ticket-card');
    const term = searchTerm.toLowerCase();
    
    tickets.forEach(ticket => {
        const content = ticket.textContent.toLowerCase();
        const shouldShow = content.includes(term);
        
        ticket.style.display = shouldShow ? 'block' : 'none';
        
        if (shouldShow) {
            ticket.style.animation = 'fadeIn 0.3s ease';
        }
    });
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { transform: translateY(100%); }
        to { transform: translateY(0); }
    }
    
    .ticket-card {
        animation: fadeIn 0.5s ease;
    }
`;
document.head.appendChild(style);