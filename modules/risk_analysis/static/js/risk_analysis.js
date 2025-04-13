/**
 * AgroSmartRisk - Risk Analysis Module
 * Frontend JS handling data retrieval, processing, and visualization
 * for the Risk Analysis section
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initializeUI();
    
    // Load parcels for dropdown
    loadParcels();
    
    // Set default dates (last 30 days)
    setDefaultDates();
    
    // Add event listeners
    registerEventListeners();
});

/**
 * Initialize UI components
 */
function initializeUI() {
    // Initialize sidebar toggling
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        });
    }
    
    // Mobile menu toggle
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.add('mobile-visible');
            sidebarBackdrop.classList.add('visible');
        });
    }
    
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', function() {
            sidebar.classList.remove('mobile-visible');
            sidebarBackdrop.classList.remove('visible');
        });
    }
    
    // Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Set default date range (last 30 days)
 */
function setDefaultDates() {
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        startDateInput.value = formatDate(thirtyDaysAgo);
        endDateInput.value = formatDate(today);
    }
}

/**
 * Format date as YYYY-MM-DD
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Load parcel data for dropdown
 */
function loadParcels() {
    fetch('/api/parcels')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(response => {
            console.log('Parcels API response:', response);
            
            const parcelSelect = document.getElementById('parcel-select');
            
            if (parcelSelect) {
                // Clear existing options
                while (parcelSelect.options.length > 0) {
                    parcelSelect.remove(0);
                }
                
                // Add default option
                const defaultOption = document.createElement('option');
                defaultOption.value = "";
                defaultOption.textContent = "Select a parcel";
                parcelSelect.appendChild(defaultOption);
                
                // Check if we have success and data properties (new format)
                const parcelsData = response.success && response.data ? response.data : response;
                
                if (Array.isArray(parcelsData) && parcelsData.length > 0) {
                    // Add parcels to select
                    parcelsData.forEach(parcel => {
                        const option = document.createElement('option');
                        option.value = parcel.id;
                        option.textContent = parcel.name;
                        option.dataset.crop = parcel.crop_type;
                        option.dataset.soil = parcel.soil_type;
                        option.dataset.area = parcel.area;
                        parcelSelect.appendChild(option);
                    });
                    
                    // Enable select
                    parcelSelect.disabled = false;
                    console.log(`Successfully loaded ${parcelsData.length} parcels`);
                } else {
                    console.error('No parcels data returned from API');
                    showErrorMessage('No parcels found in the database. Please add some parcels.');
                }
            } else {
                console.error('Parcel select element not found with ID: parcel-select');
            }
        })
        .catch(error => {
            console.error('Error loading parcels:', error);
            showErrorMessage('Failed to load parcels. Please refresh the page.');
        });
}

/**
 * Register event listeners for UI elements
 */
function registerEventListeners() {
    // Analysis form submission
    const analysisForm = document.getElementById('analysisForm');
    if (analysisForm) {
        analysisForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadRiskData();
        });
    }
    
    // Parcel selection change
    const parcelSelect = document.getElementById('parcel-select');
    if (parcelSelect) {
        parcelSelect.addEventListener('change', function() {
            updateParcelInfo();
            
            if (this.value) {
                loadRiskSummary(this.value);
                loadRiskAlerts(this.value);
            } else {
                resetRiskSummary();
                resetRiskAlerts();
            }
        });
    }
    
    // Risk type selection change
    const riskTypeSelect = document.getElementById('risk-type-select');
    if (riskTypeSelect) {
        riskTypeSelect.addEventListener('change', function() {
            const parcelSelect = document.getElementById('parcel-select');
            if (parcelSelect.value) {
                loadRiskData();
            }
        });
    }
    
    // Date range change
    const dateRange = document.getElementById('date-range');
    if (dateRange) {
        dateRange.addEventListener('change', function() {
            const parcelSelect = document.getElementById('parcel-select');
            if (parcelSelect.value) {
                loadRiskData();
            }
        });
    }
    
    // Forecast days selection change
    const forecastDays = document.getElementById('forecastDays');
    if (forecastDays) {
        forecastDays.addEventListener('change', function() {
            const parcelSelect = document.getElementById('parcel-select');
            if (parcelSelect.value) {
                updateForecastPlot(parcelSelect.value, this.value);
            }
        });
    }
    
    // Download buttons
    const downloadButtons = [
        'downloadTimeSeriesBtn',
        'downloadComparisonBtn',
        'downloadForecastBtn',
        'downloadSeasonalBtn'
    ];
    
    downloadButtons.forEach(buttonId => {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', function() {
                downloadPlotAsImage(buttonId.replace('download', '').replace('Btn', '').toLowerCase());
            });
        }
    });
}

/**
 * Update parcel information display
 */
function updateParcelInfo() {
    const parcelSelect = document.getElementById('parcel-select');
    
    if (parcelSelect && parcelSelect.selectedOptions.length > 0) {
        const selectedOption = parcelSelect.selectedOptions[0];
        
        // Update parcel info
        document.getElementById('parcel-name').textContent = selectedOption.textContent;
        document.getElementById('parcel-crop').textContent = selectedOption.dataset.crop || 'Unknown';
        document.getElementById('parcel-soil').textContent = selectedOption.dataset.soil || 'Unknown';
        document.getElementById('parcel-area').textContent = `${parseFloat(selectedOption.dataset.area).toFixed(2)} hectares`;
    } else {
        // Reset parcel info
        document.getElementById('parcel-name').textContent = 'Select a parcel';
        document.getElementById('parcel-crop').textContent = 'Select a parcel';
        document.getElementById('parcel-soil').textContent = 'Select a parcel';
        document.getElementById('parcel-area').textContent = 'Select a parcel';
    }
}

/**
 * Load risk data and update plots
 */
function loadRiskData() {
    const parcelId = document.getElementById('parcel-select').value;
    const riskType = document.getElementById('risk-type-select').value;
    const dateRange = document.getElementById('date-range').value;
    
    if (!parcelId) {
        showErrorMessage('Please select a parcel.');
        return;
    }
    
    // Show loading indicators for all plots
    document.getElementById('time-series-loading').style.display = 'flex';
    document.getElementById('comparison-loading').style.display = 'flex';
    document.getElementById('forecast-loading').style.display = 'flex';
    document.getElementById('seasonal-loading').style.display = 'flex';
    
    // Calculate date range based on selection
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - parseInt(dateRange));
    
    const formattedStartDate = formatDate(startDate);
    const formattedEndDate = formatDate(endDate);
    
    // Fetch risk data from API
    const url = `/api/risk-data/${parcelId}?risk_type=${riskType}&start_date=${formattedStartDate}&end_date=${formattedEndDate}`;
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('Successfully loaded risk data:', data);
                
                // Update all plots with the data
                updateTimeSeries(data.data, riskType);
                updateComparisonPlot(data.data, riskType);
                updateForecastPlot(data.data, riskType);
                updateSeasonalPlot(data.data, riskType);
                
                // Load summary and alerts
                loadRiskSummary(parcelId);
                loadRiskAlerts(parcelId);
            } else {
                console.error('Error loading risk data:', data.error);
                showErrorMessage(data.error || 'Failed to load risk data.');
                resetPlots();
            }
        })
        .catch(error => {
            console.error('Error loading risk data:', error);
            showErrorMessage('Failed to load risk data. Please try again.');
            resetPlots();
        })
        .finally(() => {
            // Hide all loading indicators
            document.getElementById('time-series-loading').style.display = 'none';
            document.getElementById('comparison-loading').style.display = 'none';
            document.getElementById('forecast-loading').style.display = 'none';
            document.getElementById('seasonal-loading').style.display = 'none';
        });
}

/**
 * Update time series plot with risk data
 */
function updateTimeSeries(data, riskType) {
    const plotContainer = document.getElementById('time-series-plot');
    
    if (!plotContainer) {
        console.error('Plot container not found');
        return;
    }
    
    if (!data || data.length === 0) {
        plotContainer.innerHTML = '<div class="text-center p-5"><p>No data available for the selected parameters.</p></div>';
        return;
    }
    
    console.log(`Updating time series plot with ${data.length} data points for ${riskType}`);
    console.log('Sample data point:', data[0]);
    
    // Prepare data for plotting
    const dates = [];
    const values = [];
    
    // Map the risk type to a property name
    const riskProperty = riskType;
    
    // Extract dates and values
    data.forEach(item => {
        dates.push(item.date);
        values.push(item[riskProperty]);
    });
    
    // Define colors for different risk levels
    const colors = [];
    values.forEach(value => {
        if (value < 30) {
            colors.push('rgba(16, 185, 129, 0.8)'); // Low risk - green
        } else if (value < 70) {
            colors.push('rgba(245, 158, 11, 0.8)'); // Medium risk - orange
        } else {
            colors.push('rgba(239, 68, 68, 0.8)'); // High risk - red
        }
    });
    
    // Create trace for the plot
    const trace = {
        x: dates,
        y: values,
        type: 'scatter',
        mode: 'lines+markers',
        marker: {
            size: 8,
            color: colors
        },
        line: {
            shape: 'spline',
            width: 3,
            color: 'rgba(59, 130, 246, 0.8)' // Blue line
        },
        name: getRiskTypeName(riskType)
    };
    
    // Define layout
    const layout = {
        title: `${getRiskTypeName(riskType)} Time Series`,
        xaxis: {
            title: 'Date',
            tickangle: -45
        },
        yaxis: {
            title: 'Risk Value (%)',
            range: [0, 100]
        },
        hovermode: 'closest',
        margin: {
            l: 50,
            r: 20,
            t: 50,
            b: 80
        },
        autosize: true
    };
    
    // Plot options
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false
    };
    
    // Create the plot
    Plotly.newPlot(plotContainer, [trace], layout, config);
    
    // Also update risk summary based on the data
    updateRiskSummary(data, riskType);
}

/**
 * Get human-readable name for risk type
 */
function getRiskTypeName(riskType) {
    switch(riskType) {
        case 'drought_risk':
            return 'Drought Risk';
        case 'flood_risk':
            return 'Flood Risk';
        case 'frost_risk':
            return 'Frost Risk';
        case 'overall_risk':
        default:
            return 'Overall Risk';
    }
}

/**
 * Show error message to user
 */
function showErrorMessage(message) {
    // Could be implemented with a toast or alert component
    alert(message);
}

/**
 * Reset plots when no data is available
 */
function resetPlots() {
    // Reset all plots
    document.getElementById('time-series-plot').innerHTML = '<div class="text-center p-5"><p>No data available.</p></div>';
    document.getElementById('comparison-plot').innerHTML = '<div class="text-center p-5"><p>No data available.</p></div>';
    document.getElementById('forecast-plot').innerHTML = '<div class="text-center p-5"><p>No data available.</p></div>';
    document.getElementById('seasonal-plot').innerHTML = '<div class="text-center p-5"><p>No data available.</p></div>';
    
    // Reset risk summary
    resetRiskSummary();
}

/**
 * Update risk summary information
 */
function updateRiskSummary(data, riskType) {
    // Update risk meter and statistics
    if (!data || data.length === 0) {
        resetRiskSummary();
        return;
    }
    
    // Get the latest risk value
    const latestData = data[data.length - 1];
    const currentRisk = latestData[riskType];
    
    // Calculate average risk
    let totalRisk = 0;
    data.forEach(item => {
        totalRisk += item[riskType];
    });
    const avgRisk = totalRisk / data.length;
    
    // Calculate max risk
    let maxRisk = 0;
    data.forEach(item => {
        if (item[riskType] > maxRisk) {
            maxRisk = item[riskType];
        }
    });
    
    // Calculate risk trend (comparing first half vs second half)
    const half = Math.floor(data.length / 2);
    let firstHalfRisk = 0;
    let secondHalfRisk = 0;
    
    for (let i = 0; i < half; i++) {
        firstHalfRisk += data[i][riskType];
    }
    for (let i = half; i < data.length; i++) {
        secondHalfRisk += data[i][riskType];
    }
    
    firstHalfRisk = firstHalfRisk / half;
    secondHalfRisk = secondHalfRisk / (data.length - half);
    
    const riskTrend = secondHalfRisk - firstHalfRisk;
    
    // Count days at risk (risk > 50%)
    let daysAtRisk = 0;
    data.forEach(item => {
        if (item[riskType] >= 50) {
            daysAtRisk++;
        }
    });
    
    // Update UI elements
    const riskMarker = document.getElementById('risk-marker');
    const riskPercentage = document.getElementById('risk-percentage');
    const avgRiskElement = document.getElementById('avg-risk');
    const maxRiskElement = document.getElementById('max-risk');
    const riskTrendElement = document.getElementById('risk-trend');
    const daysAtRiskElement = document.getElementById('days-at-risk');
    
    if (riskMarker) riskMarker.style.left = `${currentRisk}%`;
    if (riskPercentage) riskPercentage.textContent = `${currentRisk.toFixed(1)}%`;
    if (avgRiskElement) avgRiskElement.textContent = `${avgRisk.toFixed(1)}%`;
    if (maxRiskElement) maxRiskElement.textContent = `${maxRisk.toFixed(1)}%`;
    
    if (riskTrendElement) {
        if (riskTrend > 1) {
            riskTrendElement.innerHTML = '<i class="fas fa-arrow-up text-danger"></i>';
        } else if (riskTrend < -1) {
            riskTrendElement.innerHTML = '<i class="fas fa-arrow-down text-success"></i>';
        } else {
            riskTrendElement.innerHTML = '<i class="fas fa-minus text-muted"></i>';
        }
    }
    
    if (daysAtRiskElement) daysAtRiskElement.textContent = daysAtRisk;
}

/**
 * Reset risk summary when no data is available
 */
function resetRiskSummary() {
    const riskMarker = document.getElementById('risk-marker');
    const riskPercentage = document.getElementById('risk-percentage');
    const avgRiskElement = document.getElementById('avg-risk');
    const maxRiskElement = document.getElementById('max-risk');
    const riskTrendElement = document.getElementById('risk-trend');
    const daysAtRiskElement = document.getElementById('days-at-risk');
    
    if (riskMarker) riskMarker.style.left = '0%';
    if (riskPercentage) riskPercentage.textContent = '---';
    if (avgRiskElement) avgRiskElement.textContent = '---';
    if (maxRiskElement) maxRiskElement.textContent = '---';
    if (riskTrendElement) riskTrendElement.innerHTML = '<i class="fas fa-minus text-muted"></i>';
    if (daysAtRiskElement) daysAtRiskElement.textContent = '---';
}

/**
 * Update Comparison Plot
 */
function updateComparisonPlot(data, riskType) {
    const plotContainer = document.getElementById('comparison-plot');
    
    if (!plotContainer) {
        console.error('Comparison plot container not found');
        return;
    }
    
    if (!data || data.length === 0) {
        plotContainer.innerHTML = '<div class="text-center p-5"><p>No data available for comparison.</p></div>';
        return;
    }
    
    console.log(`Updating comparison plot with ${data.length} data points`);
    
    // Create traces for all risk types
    const dates = data.map(item => item.date);
    
    const droughtData = {
        x: dates,
        y: data.map(item => item.drought_risk),
        type: 'scatter',
        mode: 'lines',
        name: 'Drought Risk',
        line: {
            color: 'rgba(239, 68, 68, 0.8)',
            width: 2
        }
    };
    
    const floodData = {
        x: dates,
        y: data.map(item => item.flood_risk),
        type: 'scatter',
        mode: 'lines',
        name: 'Flood Risk',
        line: {
            color: 'rgba(59, 130, 246, 0.8)',
            width: 2
        }
    };
    
    const frostData = {
        x: dates,
        y: data.map(item => item.frost_risk),
        type: 'scatter',
        mode: 'lines',
        name: 'Frost Risk',
        line: {
            color: 'rgba(16, 185, 129, 0.8)',
            width: 2
        }
    };
    
    const overallData = {
        x: dates,
        y: data.map(item => item.overall_risk),
        type: 'scatter',
        mode: 'lines',
        name: 'Overall Risk',
        line: {
            color: 'rgba(139, 92, 246, 0.8)',
            width: 3,
            dash: 'dot'
        }
    };
    
    // Define layout
    const layout = {
        title: 'Risk Type Comparison',
        xaxis: {
            title: 'Date',
            tickangle: -45
        },
        yaxis: {
            title: 'Risk Value (%)',
            range: [0, 100]
        },
        hovermode: 'closest',
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: {
            l: 50,
            r: 20,
            t: 50,
            b: 100
        },
        autosize: true
    };
    
    // Plot options
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false
    };
    
    // Create the plot with all traces
    Plotly.newPlot(plotContainer, [droughtData, floodData, frostData, overallData], layout, config);
}

/**
 * Update Forecast Plot
 */
function updateForecastPlot(data, riskType) {
    const plotContainer = document.getElementById('forecast-plot');
    
    if (!plotContainer) {
        console.error('Forecast plot container not found');
        return;
    }
    
    if (!data || data.length === 0) {
        plotContainer.innerHTML = '<div class="text-center p-5"><p>No data available for forecasting.</p></div>';
        return;
    }
    
    console.log(`Updating forecast plot with ${data.length} data points for ${riskType}`);
    
    // Use the data we have to create a simple forecast
    const dates = data.map(item => new Date(item.date));
    const values = data.map(item => item[riskType]);
    
    // Sort by date (ascending)
    const sortedPairs = dates.map((date, index) => [date, values[index]])
        .sort((a, b) => a[0] - b[0]);
    
    const sortedDates = sortedPairs.map(pair => pair[0]);
    const sortedValues = sortedPairs.map(pair => pair[1]);
    
    // Generate forecast dates (next 30 days)
    const lastDate = sortedDates[sortedDates.length - 1];
    const forecastDates = [];
    const forecastValues = [];
    
    // Simple forecasting using moving average
    const windowSize = 7; // 7-day moving average
    const actualData = {
        x: sortedDates.map(d => d.toISOString().split('T')[0]),
        y: sortedValues,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Actual Data',
        line: {
            color: 'rgba(59, 130, 246, 0.8)',
            width: 2
        },
        marker: {
            size: 5
        }
    };
    
    // Calculate the forecasted values using moving average
    for (let i = 0; i < 30; i++) {
        const forecastDate = new Date(lastDate);
        forecastDate.setDate(forecastDate.getDate() + i + 1);
        forecastDates.push(forecastDate);
        
        // Use last N values for moving average
        let sum = 0;
        for (let j = Math.max(0, sortedValues.length - windowSize); j < sortedValues.length; j++) {
            sum += sortedValues[j];
        }
        const avg = sum / Math.min(windowSize, sortedValues.length);
        
        // Add some randomness to the forecast (within 10% range)
        const randomFactor = 1 + (Math.random() * 0.2 - 0.1); // -10% to +10%
        const forecastedValue = avg * randomFactor;
        
        // Ensure within 0-100 range
        forecastValues.push(Math.max(0, Math.min(100, forecastedValue)));
        
        // Add to the sorted values for the next iteration
        sortedValues.push(forecastedValue);
        sortedDates.push(forecastDate);
    }
    
    const forecastData = {
        x: forecastDates.map(d => d.toISOString().split('T')[0]),
        y: forecastValues,
        type: 'scatter',
        mode: 'lines',
        name: 'Forecasted Data',
        line: {
            color: 'rgba(239, 68, 68, 0.8)',
            width: 2,
            dash: 'dash'
        }
    };
    
    // Define layout
    const layout = {
        title: `${getRiskTypeName(riskType)} Forecast (Next 30 Days)`,
        xaxis: {
            title: 'Date',
            tickangle: -45
        },
        yaxis: {
            title: 'Risk Value (%)',
            range: [0, 100]
        },
        hovermode: 'closest',
        legend: {
            orientation: 'h',
            y: -0.2
        },
        shapes: [{
            type: 'line',
            x0: lastDate.toISOString().split('T')[0],
            y0: 0,
            x1: lastDate.toISOString().split('T')[0],
            y1: 100,
            line: {
                color: 'rgba(0, 0, 0, 0.3)',
                width: 1,
                dash: 'dot'
            }
        }],
        annotations: [{
            x: lastDate.toISOString().split('T')[0],
            y: 100,
            text: 'Forecast Begins',
            showarrow: false,
            font: {
                size: 12
            },
            xanchor: 'left',
            yanchor: 'top'
        }],
        margin: {
            l: 50,
            r: 20,
            t: 50,
            b: 100
        },
        autosize: true
    };
    
    // Plot options
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false
    };
    
    // Create the plot
    Plotly.newPlot(plotContainer, [actualData, forecastData], layout, config);
}

/**
 * Update Seasonal Plot
 */
function updateSeasonalPlot(data, riskType) {
    const plotContainer = document.getElementById('seasonal-plot');
    
    if (!plotContainer) {
        console.error('Seasonal plot container not found');
        return;
    }
    
    if (!data || data.length === 0) {
        plotContainer.innerHTML = '<div class="text-center p-5"><p>No data available for seasonal analysis.</p></div>';
        return;
    }
    
    console.log(`Updating seasonal plot with ${data.length} data points for ${riskType}`);
    
    // Group data by month
    const monthlyData = {};
    
    data.forEach(item => {
        const date = new Date(item.date);
        const month = date.getMonth(); // 0-11
        
        if (!monthlyData[month]) {
            monthlyData[month] = [];
        }
        
        monthlyData[month].push(item[riskType]);
    });
    
    // Calculate average by month
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const avgByMonth = [];
    const countByMonth = [];
    
    for (let i = 0; i < 12; i++) {
        if (monthlyData[i] && monthlyData[i].length > 0) {
            const sum = monthlyData[i].reduce((a, b) => a + b, 0);
            avgByMonth.push(sum / monthlyData[i].length);
            countByMonth.push(monthlyData[i].length);
        } else {
            avgByMonth.push(null);
            countByMonth.push(0);
        }
    }
    
    // Create bar chart
    const trace = {
        x: months,
        y: avgByMonth,
        type: 'bar',
        marker: {
            color: avgByMonth.map(val => {
                if (val === null) return 'rgba(200, 200, 200, 0.5)';
                if (val < 30) return 'rgba(16, 185, 129, 0.8)';
                if (val < 70) return 'rgba(245, 158, 11, 0.8)';
                return 'rgba(239, 68, 68, 0.8)';
            })
        },
        text: countByMonth.map(count => `${count} data points`),
        hoverinfo: 'y+text'
    };
    
    // Define layout
    const layout = {
        title: `${getRiskTypeName(riskType)} - Seasonal Pattern`,
        xaxis: {
            title: 'Month'
        },
        yaxis: {
            title: 'Average Risk Value (%)',
            range: [0, 100]
        },
        margin: {
            l: 50,
            r: 20,
            t: 50,
            b: 80
        },
        autosize: true
    };
    
    // Plot options
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false
    };
    
    // Create the plot
    Plotly.newPlot(plotContainer, [trace], layout, config);
}

// These functions would be implemented to complete the full functionality
function loadRiskSummary(parcelId) {
    // Implementation for loading risk summary
}

function resetRiskSummary() {
    // Implementation for resetting risk summary
}

function loadRiskAlerts(parcelId) {
    // Implementation for loading risk alerts
}

function resetRiskAlerts() {
    // Implementation for resetting risk alerts
}

function downloadPlotAsImage(plotType) {
    // Implementation for downloading plot as image
}
