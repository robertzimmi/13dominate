// winsChart.js

// Receber os dados que serão definidos no template (global)
const chartLabels = window.chartLabels || [];
const chartWins = window.chartWins || [];

const ctx = document.getElementById('winsChart').getContext('2d');
const winsChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: chartLabels,
    datasets: [{
      label: 'Vitórias',
      data: chartWins,
      fill: false,
      borderColor: 'rgba(54, 162, 235, 1)',
      backgroundColor: 'rgba(54, 162, 235, 0.6)',
      borderWidth: 2,
      tension: 0.3,
      pointRadius: 5,
      pointHoverRadius: 7
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function(context) {
            return context.parsed.y + ' vitória(s)';
          }
        }
      }
    },
    scales: {
      x: {
        title: { display: true, text: 'Data' }
      },
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Vitórias' },
        ticks: { stepSize: 1 }
      }
    }
  }
});
