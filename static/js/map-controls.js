/**
 * Map Controls for AgroSmartRisk
 * This file handles the custom map controls for the AgroSmartRisk application
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Map controls initialized');
    
    // Function to handle map iframe ready state
    function setupMapControls() {
        // Create custom map controls
        createCustomControls();
        
        // Set up time controls
        setupTimeControls();
        
        // Listen for messages from the map iframe
        window.addEventListener('message', function(event) {
            if (event.data && event.data.status === 'mapReady') {
                console.log('Map is ready, controls can now be used');
            }
        });
    }
    
    // Function to create custom map controls
    function createCustomControls() {
        const mapContainer = document.getElementById('map-container');
        if (!mapContainer) {
            console.error('Map container not found');
            return;
        }
        
        // Create controls container
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'map-controls';
        controlsContainer.innerHTML = `
            <div class="d-flex flex-column">
                <button class="map-control-btn mb-2" id="zoom-in" aria-label="Zoom in">
                    <i class="fas fa-search-plus"></i>
                </button>
                <button class="map-control-btn mb-2" id="zoom-out" aria-label="Zoom out">
                    <i class="fas fa-search-minus"></i>
                </button>
                <button class="map-control-btn mb-2" id="reset-map" aria-label="Reset map view">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button class="map-control-btn" id="toggle-layers" aria-label="Toggle layers">
                    <i class="fas fa-layer-group"></i>
                </button>
            </div>
        `;
        
        // Add controls to map container
        mapContainer.appendChild(controlsContainer);
        
        // Add event listeners to buttons
        setupControlListeners();
    }
    
    // Function to set up event listeners for map controls
    function setupControlListeners() {
        // Get control buttons
        const zoomInBtn = document.getElementById('zoom-in');
        const zoomOutBtn = document.getElementById('zoom-out');
        const resetMapBtn = document.getElementById('reset-map');
        const toggleLayersBtn = document.getElementById('toggle-layers');
        
        // Add event listeners
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', function(e) {
                e.preventDefault();
                sendMapCommand('zoomIn');
            });
        }
        
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', function(e) {
                e.preventDefault();
                sendMapCommand('zoomOut');
            });
        }
        
        if (resetMapBtn) {
            resetMapBtn.addEventListener('click', function(e) {
                e.preventDefault();
                sendMapCommand('resetMap');
            });
        }
        
        if (toggleLayersBtn) {
            toggleLayersBtn.addEventListener('click', function(e) {
                e.preventDefault();
                sendMapCommand('toggleLayers');
            });
        }
    }
    
    // Function to send commands to the map iframe
    function sendMapCommand(command) {
        console.log('Sending command to map:', command);
        const mapFrame = document.getElementById('map-frame');
        
        if (mapFrame && mapFrame.contentWindow) {
            mapFrame.contentWindow.postMessage({ command: command }, '*');
        } else {
            console.error('Map frame not found or not ready');
        }
    }
    
    // Initialize map controls
    setupMapControls();
    
    // Function to set up time controls
    function setupTimeControls() {
        const playButton = document.getElementById('play-button');
        const backwardButton = document.querySelector('.timecontrol-backward');
        const forwardButton = document.querySelector('.timecontrol-forward');
        const loopButton = document.querySelector('.timecontrol-loop');
        const dateDisplay = document.querySelector('.timecontrol-date');
        const dateSlider = document.querySelector('.timecontrol-dateslider .knob');
        const speedSlider = document.querySelector('.timecontrol-speed .knob');
        
        // Get all available dates from the date selector
        const dateSelector = document.getElementById('date-selector');
        const allDates = Array.from(dateSelector.options).map(option => option.value);
        let currentDateIndex = 0;
        let isPlaying = false;
        let animationInterval;
        let isLooping = false;
        
        // Update the date display
        function updateDateDisplay(date) {
            if (dateDisplay) {
                dateDisplay.textContent = date;
                // Also update the current-date element if it exists
                const currentDateElement = document.getElementById('current-date');
                if (currentDateElement) {
                    // Format date for display (e.g., January 15, 2025)
                    const dateObj = new Date(date);
                    currentDateElement.textContent = dateObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
                }
            }
        }
        
        // Update the slider position
        function updateSliderPosition() {
            if (dateSlider && allDates.length > 0) {
                const percentage = (currentDateIndex / (allDates.length - 1)) * 100;
                dateSlider.style.transform = `translate3d(${percentage}%, 0px, 0px)`;
            }
        }
        
        // Make the slider interactive
        function setupSliderInteraction() {
            const sliderContainer = document.querySelector('.timecontrol-dateslider .slider');
            if (!sliderContainer) return;
            
            // Function to calculate date index from slider position
            function getDateIndexFromPosition(clientX) {
                const rect = sliderContainer.getBoundingClientRect();
                const position = (clientX - rect.left) / rect.width;
                const clampedPosition = Math.max(0, Math.min(1, position));
                return Math.round(clampedPosition * (allDates.length - 1));
            }
            
            // Handle mouse/touch events
            let isDragging = false;
            
            sliderContainer.addEventListener('mousedown', function(e) {
                isDragging = true;
                currentDateIndex = getDateIndexFromPosition(e.clientX);
                loadCurrentDate();
            });
            
            document.addEventListener('mousemove', function(e) {
                if (isDragging) {
                    currentDateIndex = getDateIndexFromPosition(e.clientX);
                    loadCurrentDate();
                }
            });
            
            document.addEventListener('mouseup', function() {
                isDragging = false;
            });
            
            // Touch events for mobile
            sliderContainer.addEventListener('touchstart', function(e) {
                isDragging = true;
                currentDateIndex = getDateIndexFromPosition(e.touches[0].clientX);
                loadCurrentDate();
            });
            
            document.addEventListener('touchmove', function(e) {
                if (isDragging) {
                    currentDateIndex = getDateIndexFromPosition(e.touches[0].clientX);
                    loadCurrentDate();
                }
            });
            
            document.addEventListener('touchend', function() {
                isDragging = false;
            });
        }
        
        // Load the map for the current date
        function loadCurrentDate() {
            if (allDates.length > 0 && currentDateIndex >= 0 && currentDateIndex < allDates.length) {
                const currentDate = allDates[currentDateIndex];
                dateSelector.value = currentDate;
                
                // Trigger the change event on the date selector
                const event = new Event('change');
                dateSelector.dispatchEvent(event);
                
                // Update the date display
                updateDateDisplay(currentDate);
                
                // Update the slider position
                updateSliderPosition();
            }
        }
        
        // Play/Pause animation
        function togglePlay() {
            if (isPlaying) {
                // Stop animation
                clearInterval(animationInterval);
                playButton.classList.remove('pause');
                playButton.classList.add('play');
                isPlaying = false;
            } else {
                // Start animation
                playButton.classList.remove('play');
                playButton.classList.add('pause');
                isPlaying = true;
                
                animationInterval = setInterval(() => {
                    // Move to next date
                    currentDateIndex++;
                    
                    // Check if we've reached the end
                    if (currentDateIndex >= allDates.length) {
                        if (isLooping) {
                            // Loop back to start
                            currentDateIndex = 0;
                        } else {
                            // Stop at the end
                            currentDateIndex = allDates.length - 1;
                            togglePlay(); // Stop playing
                            return;
                        }
                    }
                    
                    // Load the current date
                    loadCurrentDate();
                }, 1500); // Advance every 1.5 seconds
            }
        }
        
        // Move backward one step
        function moveBackward() {
            currentDateIndex = Math.max(0, currentDateIndex - 1);
            loadCurrentDate();
        }
        
        // Move forward one step
        function moveForward() {
            currentDateIndex = Math.min(allDates.length - 1, currentDateIndex + 1);
            loadCurrentDate();
        }
        
        // Toggle loop mode
        function toggleLoop() {
            isLooping = !isLooping;
            if (isLooping) {
                loopButton.classList.add('looped');
            } else {
                loopButton.classList.remove('looped');
            }
        }
        
        // Add event listeners
        if (playButton) {
            playButton.addEventListener('click', function(e) {
                e.preventDefault();
                togglePlay();
            });
        }
        
        if (backwardButton) {
            backwardButton.addEventListener('click', function(e) {
                e.preventDefault();
                moveBackward();
            });
        }
        
        if (forwardButton) {
            forwardButton.addEventListener('click', function(e) {
                e.preventDefault();
                moveForward();
            });
        }
        
        if (loopButton) {
            loopButton.addEventListener('click', function(e) {
                e.preventDefault();
                toggleLoop();
            });
        }
        
        // Initialize with the first date
        loadCurrentDate();
        
        // Set up interactive slider
        setupSliderInteraction();
    }
});
