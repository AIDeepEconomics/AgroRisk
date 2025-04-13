/**
 * AgroSmartRisk Time-Series Analysis Frontend JavaScript
 * Handles API interactions and data visualization
 */

// Global variables
let selectedParcel = null;
let selectedRiskType = 'overall';
let chartInstances = {};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Fetch parcels data for dropdown
    fetchParcels();
    
    // Set up event listeners
    setupEventListeners();
});

/**
 * Sets up event listeners for UI interactions
 */
function setupEventListeners() {
    // Parcel selection change
    document.getElementById('parcel-select').addEventListener('change', function() {
        selectedParcel = this.value;
        if (selectedParcel) {
            loadParcelData(selectedParcel);
        }
    });
    
    // Risk type selection
    document.querySelectorAll('input[name="risk-type"]').forEach(input => {
        input.addEventListener('change', function() {
            selectedRiskType = this.value;
            if (selectedParcel) {
                updateCharts(selectedParcel, selectedRiskType);
            }
        });
    });
    
    // Time period buttons
    document.querySelectorAll('.time-period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.time-period-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const days = parseInt(this.dataset.days);
            if (selectedParcel) {
                filterDataByDays(days);
            }
        });
    });
    
    // Analysis type tabs
    document.querySelectorAll('.analysis-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.analysis-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            document.querySelectorAll('.analysis-content').forEach(content => {
                content.style.display = 'none';
            });
            
            document.getElementById(this.dataset.target).style.display = 'block';
            
            if (selectedParcel) {
                const analysisType = this.dataset.analysis;
                loadAnalysisData(selectedParcel, selectedRiskType, analysisType);
            }
        });
    });
}

/**
 * Fetches list of parcels from API
 */
function fetchParcels() {
    fetch('/api/parcels')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateParcelDropdown(data.parcels);
            } else {
                showError('Failed to load parcels: ' + data.error);
            }
        })
        .catch(error => {
            showError('Error connecting to server: ' + error);
        });
}

/**
 * Populates parcel dropdown with data from API
 */
function populateParcelDropdown(parcels) {
    const select = document.getElementById('parcel-select');
    select.innerHTML = '<option value="">Select a parcel</option>';
    
    parcels.forEach(parcel => {
        const option = document.createElement('option');
        option.value = parcel.id;
        option.textContent = `Parcel ${parcel.id}: ${parcel.crop_type} (${parcel.area.toFixed(2)} ha)`;
        select.appendChild(option);
    });
}

/**
 * Loads data for a selected parcel
 */
function loadParcelData(parcelId) {
    fetch(`/api/parcels/${parcelId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayParcelInfo(data.parcel);
                loadRiskData(parcelId, selectedRiskType);
            } else {
                showError('Failed to load parcel data: ' + data.error);
            }
        })
        .catch(error => {
            showError('Error connecting to server: ' + error);
        });
}

/**
 * Displays parcel information in the UI
 */
function displayParcelInfo(parcel) {
    document.getElementById('parcel-details').innerHTML = `
        <h3>Parcel ${parcel.id}</h3>
        <p><strong>Location:</strong> ${parcel.location}</p>
        <p><strong>Area:</strong> ${parcel.area.toFixed(2)} hectares</p>
        <p><strong>Crop Type:</strong> ${parcel.crop_type}</p>
        <p><strong>Soil Type:</strong> ${parcel.soil_type}</p>
    `;
    
    // Show the dashboard
    document.getElementById('dashboard').classList.remove('hidden');
}

/**
 * Loads risk data for a parcel
 */
function loadRiskData(parcelId, riskType) {
    fetch(`/api/risk-data?parcel_id=${parcelId}&risk_type=${riskType}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderRiskChart(data.risk_data, riskType);
                updateCharts(parcelId, riskType);
            } else {
                showError('Failed to load risk data: ' + data.error);
            }
        })
        .catch(error => {
            showError('Error connecting to server: ' + error);
        });
}

/**
 * Renders the main risk chart
 */
function renderRiskChart(riskData, riskType) {
    const dates = riskData.map(d => new Date(d.date));
    const values = riskData.map(d => d[riskType + '_risk'] || d.overall_risk);
    
    const ctx = document.getElementById('risk-chart').getContext('2d');
    
    if (chartInstances.riskChart) {
        chartInstances.riskChart.destroy();
    }
    
    chartInstances.riskChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: capitalize(riskType) + ' Risk Index',
                data: values,
                borderColor: getRiskColor(riskType),
                backgroundColor: getRiskColor(riskType, 0.2),
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    min: 0,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Risk Index (%)'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Helper to get risk color based on type
 */
function getRiskColor(riskType, alpha = 1) {
    const colors = {
        overall: `rgba(33, 150, 243, ${alpha})`,
        drought: `rgba(255, 152, 0, ${alpha})`,
        flood: `rgba(3, 169, 244, ${alpha})`,
        frost: `rgba(156, 39, 176, ${alpha})`,
        pest: `rgba(76, 175, 80, ${alpha})`
    };
    
    return colors[riskType] || colors.overall;
}

/**
 * Capitalize first letter of string
 */
function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Updates all charts based on selected parcel and risk type
 */
function updateCharts(parcelId, riskType) {
    // Update for each analysis type
    loadAnalysisData(parcelId, riskType, 'change-points');
    loadAnalysisData(parcelId, riskType, 'seasonal');
    loadAnalysisData(parcelId, riskType, 'forecast');
    loadAnalysisData(parcelId, riskType, 'patterns');
    loadAnalysisData(parcelId, riskType, 'volatility');
}

/**
 * Loads specific analysis data
 */
function loadAnalysisData(parcelId, riskType, analysisType) {
    let endpoint = '';
    switch(analysisType) {
        case 'change-points':
            endpoint = `/api/risk-data/change-points?parcel_id=${parcelId}&risk_type=${riskType}`;
            break;
        case 'seasonal':
            endpoint = `/api/risk-data/seasonal-decomposition?parcel_id=${parcelId}&risk_type=${riskType}`;
            break;
        case 'forecast':
            endpoint = `/api/risk-data/arima-forecast?parcel_id=${parcelId}&risk_type=${riskType}`;
            break;
        case 'patterns':
            endpoint = `/api/risk-data/patterns?parcel_id=${parcelId}&risk_type=${riskType}`;
            break;
        case 'volatility':
            endpoint = `/api/risk-data/volatility?parcel_id=${parcelId}&risk_type=${riskType}`;
            break;
        default:
            return;
    }
    
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                switch(analysisType) {
                    case 'change-points':
                        renderChangePointsChart(data);
                        break;
                    case 'seasonal':
                        renderSeasonalChart(data);
                        break;
                    case 'forecast':
                        renderForecastChart(data);
                        break;
                    case 'patterns':
                        renderPatternsChart(data);
                        break;
                    case 'volatility':
                        renderVolatilityChart(data);
                        break;
                }
            } else {
                showError(`Failed to load ${analysisType} data: ${data.error}`);
            }
        })
        .catch(error => {
            showError(`Error connecting to server for ${analysisType}: ${error}`);
        });
}

/**
 * Shows error message to user
 */
function showError(message) {
    const errorDiv = document.getElementById('error-messages');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

// Additional helper functions for rendering specific chart types would go here
