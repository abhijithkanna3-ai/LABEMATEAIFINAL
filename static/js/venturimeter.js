class VenturimeterCalculator {
    constructor() {
        this.trialCount = 0;
        this.results = null;
        this.initializeEventListeners();
        this.addTrial(); // Add first trial by default
    }

    initializeEventListeners() {
        // Calculate button
        document.getElementById('calculateBtn').addEventListener('click', () => {
            this.calculateResults();
        });

        // Add trial button
        document.getElementById('addTrial').addEventListener('click', () => {
            this.addTrial();
        });

        // Load sample data
        document.getElementById('loadSampleData').addEventListener('click', () => {
            this.loadSampleData();
        });

        // Clear all data
        document.getElementById('clearAllData').addEventListener('click', () => {
            this.clearAllData();
        });

        // Export results
        document.getElementById('exportResults').addEventListener('click', () => {
            this.exportResults();
        });
    }

    addTrial() {
        this.trialCount++;
        const container = document.getElementById('readingsContainer');
        
        const trialDiv = document.createElement('div');
        trialDiv.className = 'trial-input mb-3 p-3 border rounded';
        trialDiv.id = `trial-${this.trialCount}`;
        
        trialDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0 text-primary">Trial ${this.trialCount}</h6>
                <button type="button" class="btn btn-outline-danger btn-sm remove-trial" data-trial="${this.trialCount}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="row g-3">
                <div class="col-md-4">
                    <label class="form-label">h₁ (cm)</label>
                    <input type="number" class="form-control trial-h1" step="0.1" placeholder="Enter h₁">
                </div>
                <div class="col-md-4">
                    <label class="form-label">h₂ (cm)</label>
                    <input type="number" class="form-control trial-h2" step="0.1" placeholder="Enter h₂">
                </div>
                <div class="col-md-4">
                    <label class="form-label">t (seconds)</label>
                    <input type="number" class="form-control trial-t" step="0.1" placeholder="Enter time">
                </div>
            </div>
        `;
        
        container.appendChild(trialDiv);
        
        // Add remove trial event listener
        trialDiv.querySelector('.remove-trial').addEventListener('click', (e) => {
            this.removeTrial(e.target.dataset.trial);
        });
    }

    removeTrial(trialId) {
        const trialElement = document.getElementById(`trial-${trialId}`);
        if (trialElement) {
            trialElement.remove();
        }
    }

    loadSampleData() {
        // Set constants
        document.getElementById('d1').value = '19';
        document.getElementById('d2').value = '9.55';
        document.getElementById('tank_length').value = '0.49';
        document.getElementById('tank_width').value = '0.49';
        document.getElementById('water_height').value = '0.10';
        document.getElementById('conversion_factor').value = '12.6';

        // Clear existing trials
        document.getElementById('readingsContainer').innerHTML = '';
        this.trialCount = 0;

        // Add sample trials (h1 > h2 for proper Venturimeter operation)
        const sampleData = [
            { h1: 25.5, h2: 18.2, t: 45.2 },
            { h1: 28.1, h2: 16.8, t: 42.1 },
            { h1: 26.8, h2: 17.5, t: 43.8 },
            { h1: 27.3, h2: 17.1, t: 44.5 },
            { h1: 25.9, h2: 18.0, t: 45.8 }
        ];

        sampleData.forEach((data, index) => {
            this.addTrial();
            const trialElement = document.getElementById(`trial-${this.trialCount}`);
            trialElement.querySelector('.trial-h1').value = data.h1;
            trialElement.querySelector('.trial-h2').value = data.h2;
            trialElement.querySelector('.trial-t').value = data.t;
        });
    }

    clearAllData() {
        // Reset constants to defaults
        document.getElementById('d1').value = '19';
        document.getElementById('d2').value = '9.55';
        document.getElementById('tank_length').value = '0.49';
        document.getElementById('tank_width').value = '0.49';
        document.getElementById('water_height').value = '0.10';
        document.getElementById('conversion_factor').value = '12.6';

        // Clear trials
        document.getElementById('readingsContainer').innerHTML = '';
        this.trialCount = 0;
        this.addTrial();

        // Hide results
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('exportResults').disabled = true;
    }

    validateInputs() {
        const constants = this.getConstants();
        const readings = this.getReadings();

        // Validate constants
        const requiredConstants = ['d1', 'd2', 'tank_length', 'tank_width', 'water_height', 'g', 'conversion_factor'];
        for (const constant of requiredConstants) {
            if (!constants[constant] || constants[constant] <= 0) {
                throw new Error(`Invalid or missing constant: ${constant}`);
            }
        }

        // Validate that inlet diameter is larger than throat diameter
        if (constants.d1 <= constants.d2) {
            throw new Error('Inlet diameter must be larger than throat diameter for Venturimeter to work properly');
        }

        // Validate readings
        if (readings.length === 0) {
            throw new Error('No trial readings provided');
        }

        for (let i = 0; i < readings.length; i++) {
            const reading = readings[i];
            if (!reading.h1 || !reading.h2 || !reading.t) {
                throw new Error(`Trial ${i + 1}: All fields (h₁, h₂, t) are required`);
            }
            if (reading.t <= 0) {
                throw new Error(`Trial ${i + 1}: Time must be positive`);
            }
            if (reading.h1 <= reading.h2) {
                throw new Error(`Trial ${i + 1}: h₁ (${reading.h1} cm) must be greater than h₂ (${reading.h2} cm) for proper Venturimeter operation`);
            }
        }

        return { constants, readings };
    }

    getConstants() {
        return {
            d1: parseFloat(document.getElementById('d1').value),
            d2: parseFloat(document.getElementById('d2').value),
            tank_length: parseFloat(document.getElementById('tank_length').value),
            tank_width: parseFloat(document.getElementById('tank_width').value),
            water_height: parseFloat(document.getElementById('water_height').value),
            g: 9.81, // Fixed value
            conversion_factor: parseFloat(document.getElementById('conversion_factor').value)
        };
    }

    getReadings() {
        const readings = [];
        const trialElements = document.querySelectorAll('.trial-input');
        
        trialElements.forEach((trialElement, index) => {
            const h1 = parseFloat(trialElement.querySelector('.trial-h1').value);
            const h2 = parseFloat(trialElement.querySelector('.trial-h2').value);
            const t = parseFloat(trialElement.querySelector('.trial-t').value);
            
            if (!isNaN(h1) && !isNaN(h2) && !isNaN(t)) {
                readings.push({ h1, h2, t });
            }
        });
        
        return readings;
    }

    async calculateResults() {
<<<<<<< HEAD
        let loadingModal = null;
        let timeoutId = null;
        
=======
>>>>>>> d704b12d7af1f1bfa7a332280670c64ecb7ade3b
        try {
            // Validate inputs
            const { constants, readings } = this.validateInputs();

            // Show loading modal
<<<<<<< HEAD
            loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
            loadingModal.show();

            // Set timeout to hide modal after 30 seconds
            timeoutId = setTimeout(() => {
                if (loadingModal) {
                    loadingModal.hide();
                }
                this.showError('Calculation timed out. Please try again.');
            }, 30000);

=======
            const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
            loadingModal.show();

>>>>>>> d704b12d7af1f1bfa7a332280670c64ecb7ade3b
            // Prepare data
            const requestData = {
                constants: constants,
                readings: readings
            };

            // Send request
<<<<<<< HEAD
            console.log('Sending request to /venturimeter_calculate with data:', requestData);
=======
>>>>>>> d704b12d7af1f1bfa7a332280670c64ecb7ade3b
            const response = await fetch('/venturimeter_calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

<<<<<<< HEAD
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);

            // Clear timeout
            if (timeoutId) {
                clearTimeout(timeoutId);
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Response data:', result);
            
            // Hide loading modal
            if (loadingModal) {
                loadingModal.hide();
            }
=======
            const result = await response.json();
            loadingModal.hide();
>>>>>>> d704b12d7af1f1bfa7a332280670c64ecb7ade3b

            if (result.success) {
                this.results = result;
                this.displayResults(result);
                document.getElementById('exportResults').disabled = false;
            } else {
                this.showError(result.error || 'Calculation failed');
            }

        } catch (error) {
<<<<<<< HEAD
            // Clear timeout
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
            
            // Hide loading modal
            if (loadingModal) {
                loadingModal.hide();
            }
            
            console.error('Calculation error:', error);
=======
            const loadingModal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
            if (loadingModal) {
                loadingModal.hide();
            }
>>>>>>> d704b12d7af1f1bfa7a332280670c64ecb7ade3b
            this.showError(error.message || 'An error occurred during calculation');
        }
    }

    displayResults(result) {
        // Show results section
        document.getElementById('resultsSection').style.display = 'block';

        // Update summary
        document.getElementById('meanCd').textContent = result.mean_cd;
        document.getElementById('trialCount').textContent = result.results.length;

        // Populate results table
        const tableBody = document.getElementById('resultsTable');
        tableBody.innerHTML = '';

        result.results.forEach((trial, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${trial.trial}</td>
                <td>${trial.h1.toFixed(1)}</td>
                <td>${trial.h2.toFixed(1)}</td>
                <td>${trial.t.toFixed(1)}</td>
                <td>${trial.H.toFixed(4)}</td>
                <td>${trial.Qt.toExponential(3)}</td>
                <td>${trial.Qa.toExponential(3)}</td>
                <td><strong>${trial.Cd.toFixed(4)}</strong></td>
            `;
            tableBody.appendChild(row);
        });

        // Display model calculation
        document.getElementById('modelCalculation').textContent = result.model_calculation;

        // Display graph
        if (result.graph_base64) {
            document.getElementById('graphImage').src = `data:image/png;base64,${result.graph_base64}`;
        }

        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
    }

    async exportResults() {
        if (!this.results || !this.results.pdf_base64) {
            this.showError('No results available for export');
            return;
        }

        try {
            // Convert base64 to blob
            const pdfData = atob(this.results.pdf_base64);
            const pdfBlob = new Blob([pdfData], { type: 'application/pdf' });
            
            // Create download link
            const url = URL.createObjectURL(pdfBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `venturimeter_report_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

        } catch (error) {
            this.showError('Failed to export PDF: ' + error.message);
        }
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }
}

<<<<<<< HEAD
// Global function to force close loading modal
function forceCloseLoadingModal() {
    console.log('Force closing loading modal...');
    
    // Try multiple methods to close the modal
    const loadingModal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
    if (loadingModal) {
        console.log('Closing via Bootstrap instance');
        loadingModal.hide();
    }
    
    // Also try to hide it directly
    const modalElement = document.getElementById('loadingModal');
    if (modalElement) {
        console.log('Closing via direct DOM manipulation');
        modalElement.classList.remove('show');
        modalElement.style.display = 'none';
        modalElement.setAttribute('aria-hidden', 'true');
        modalElement.removeAttribute('aria-modal');
        modalElement.removeAttribute('role');
        
        // Remove modal-open class from body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // Remove backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
        
        // Remove any remaining modal instances
        const allModals = document.querySelectorAll('.modal');
        allModals.forEach(modal => {
            modal.classList.remove('show');
            modal.style.display = 'none';
        });
    }
    
    console.log('Modal close attempt completed');
}

// Test function for debugging modal issues
function testModalClose() {
    console.log('=== MODAL DEBUG TEST ===');
    console.log('Modal element exists:', !!document.getElementById('loadingModal'));
    console.log('Modal classes:', document.getElementById('loadingModal').className);
    console.log('Modal style display:', document.getElementById('loadingModal').style.display);
    console.log('Body classes:', document.body.className);
    console.log('Backdrop exists:', !!document.querySelector('.modal-backdrop'));
    
    // Try to close it
    forceCloseLoadingModal();
    
    // Check again after close attempt
    setTimeout(() => {
        console.log('After close attempt:');
        console.log('Modal classes:', document.getElementById('loadingModal').className);
        console.log('Modal style display:', document.getElementById('loadingModal').style.display);
        console.log('Body classes:', document.body.className);
        console.log('Backdrop exists:', !!document.querySelector('.modal-backdrop'));
    }, 100);
}

// Test function for venturimeter calculation
async function testVenturimeterFunction() {
    console.log('=== TESTING VENTURIMETER FUNCTION ===');
    
    try {
        const response = await fetch('/test_venturimeter');
        const result = await response.json();
        console.log('Test result:', result);
        
        if (result.success) {
            alert('Venturimeter function test PASSED! Check console for details.');
        } else {
            alert('Venturimeter function test FAILED: ' + result.error);
        }
    } catch (error) {
        console.error('Test error:', error);
        alert('Test failed with error: ' + error.message);
    }
}

=======
>>>>>>> d704b12d7af1f1bfa7a332280670c64ecb7ade3b
// Initialize calculator when page loads
document.addEventListener('DOMContentLoaded', function() {
    new VenturimeterCalculator();
});

