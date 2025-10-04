$(document).ready(function() {
  // Initialize compliance chart
  const ctx = document.getElementById('complianceChart').getContext('2d');
  const complianceChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [{
        label: 'Compliance Score',
        data: [85, 79, 92, 88, 94, 96],
        backgroundColor: 'rgba(100, 255, 218, 0.2)',
        borderColor: 'rgba(100, 255, 218, 1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      plugins: {
        tooltip: {
          mode: 'index',
          intersect: false
        },
        legend: {
          display: false
        }
      },
      hover: {
        mode: 'nearest',
        intersect: true
      }
    }
  });

  // Date range filter functionality
  $('.date-filter button').click(function() {
    const startDate = $('#date-range-start').val();
    const endDate = $('#date-range-end').val();
    
    if (startDate && endDate) {
      // Implement AJAX call to filter data
      console.log(`Filtering from ${startDate} to ${endDate}`);
    }
  });

  // Quick actions
  $('.action-btn').click(function() {
    const action = $(this).data('action');
    
    switch(action) {
      case 'export':
        window.location.href = '/checklist/export/';
        break;
      case 'filter':
        $('#store-filter-modal').modal('show');
        break;
    }
  });
});