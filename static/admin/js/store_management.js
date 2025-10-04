// Store Management Dashboard JS
$(document).ready(function() {
    // Initialize charts
    initStoreCharts();
    
    // Set up filters
    $('.store-filter').change(function() {
        updateStoreDashboard();
    });
    
    // Set up refresh button
    $('#refresh-stores').click(function() {
        updateStoreDashboard();
    });
});

function initStoreCharts() {
    // Compliance Trend Chart
    const complianceCtx = document.getElementById('complianceChart').getContext('2d');
    new Chart(complianceCtx, {
        type: 'line',
        data: {
            labels: JSON.parse($('#compliance-labels').val()),
            datasets: [{
                label: 'Compliance %',
                data: JSON.parse($('#compliance-data').val()),
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function updateStoreDashboard() {
    const filters = {
        region: $('#region-filter').val(),
        status: $('#status-filter').val(),
        compliance: $('#compliance-filter').val()
    };
    
    $.ajax({
        url: '/admin/store-analytics/',
        data: filters,
        success: function(data) {
            // Update dashboard stats
            $('#total-stores').text(data.total_stores);
            $('#active-stores').text(data.active_stores);
            $('#avg-compliance').text(data.avg_compliance + '%');
            $('#open-actions').text(data.open_actions);
            
            // Update charts
            updateCharts(data.chart_data);
        }
    });
}