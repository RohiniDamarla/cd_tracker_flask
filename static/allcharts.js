console.log('✅ allcharts.js loaded and running');

document.querySelectorAll('.bank-name').forEach((el) => {
  el.addEventListener('click', () => {
    const row = el.closest('tr');
    const chartRow = row.nextElementSibling;
    chartRow.style.display = chartRow.style.display === 'none' ? '' : 'none';

    const cdId = row.getAttribute('data-id');
    if (!cdId) {
      console.error('Missing CD ID');
      return;
    }

    try {
      const amount = parseFloat(row.children[1].innerText);
      const rate = parseFloat(row.children[2].innerText);
      const startDate = new Date(row.children[3].innerText);
      const maturityDate = new Date(row.children[4].innerText);

      if (isNaN(amount) || isNaN(rate) || isNaN(startDate) || isNaN(maturityDate)) {
        console.error('Invalid CD data:', { amount, rate, startDate, maturityDate });
        return;
      }

      const labels = [];
      const data = [];

      let currentDate = new Date(startDate);
      while (currentDate <= maturityDate) {
        const monthsElapsed = (currentDate.getFullYear() - startDate.getFullYear()) * 12 +
                              (currentDate.getMonth() - startDate.getMonth());
        const years = monthsElapsed / 12;
        const interest = amount * (rate / 100) * years;
        const total = amount + interest;

        const label = `${currentDate.toLocaleString('default', { month: 'short' })} ${currentDate.getFullYear()}`;
        labels.push(label);
        data.push(parseFloat(total.toFixed(2)));

        currentDate.setMonth(currentDate.getMonth() + 1);
      }

      const barCanvas = document.getElementById(`bar-chart-${cdId}`);
      const lineCanvas = document.getElementById(`line-chart-${cdId}`);
      const pieCanvas = document.getElementById(`pie-chart-${cdId}`);

      if (!barCanvas || !lineCanvas || !pieCanvas) {
        console.error('Missing canvas elements for CD ID:', cdId);
        return;
      }

      if (!barCanvas.dataset.rendered) {
        // Bar Chart
        new Chart(barCanvas, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Total Value ($)',
              data: data,
              backgroundColor: '#4CAF50'
            }]
          },
          options: {
            scales: {
              x: {
                title: { display: true, text: 'Month-Year' },
                ticks: { autoSkip: false, maxRotation: 90, minRotation: 45 }
              },
              y: {
                title: { display: true, text: 'Total Value ($)' },
                beginAtZero: true
              }
            },
            plugins: {
              title: {
                display: true,
                text: 'CD Growth Over Time (Bar Chart)'
              },
              legend: { display: false }
            }
          }
        });

        // Line Chart
        new Chart(lineCanvas, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: 'Total Value ($)',
              data: data,
              borderColor: '#FF5722',
              fill: false,
              tension: 0.3
            }]
          },
          options: {
            scales: {
              x: {
                title: { display: true, text: 'Month-Year' },
                ticks: { autoSkip: false, maxRotation: 90, minRotation: 45 }
              },
              y: {
                title: { display: true, text: 'Total Value ($)' },
                beginAtZero: true
              }
            },
            plugins: {
              title: {
                display: true,
                text: 'CD Value Growth (Line Chart)'
              }
            }
          }
        });

        // Pie Chart (at maturity)
        const finalValue = data[data.length - 1];
        const interestEarned = finalValue - amount;

        new Chart(pieCanvas, {
          type: 'pie',
          data: {
            labels: ['Principal', 'Interest'],
            datasets: [{
              data: [amount, interestEarned],
              backgroundColor: ['#4CAF50', '#2196F3']
            }]
          },
          options: {
            plugins: {
              title: {
                display: true,
                text: 'Principal vs Interest at Maturity'
              }
            }
          }
        });

        // Mark as rendered
        barCanvas.dataset.rendered = true;
        lineCanvas.dataset.rendered = true;
        pieCanvas.dataset.rendered = true;
      }
    } catch (err) {
      console.error('Chart rendering failed:', err);
    }
  });
});