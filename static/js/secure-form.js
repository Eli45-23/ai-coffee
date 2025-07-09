/**
 * AIChatFlows - Secure Form Handler
 * Security-hardened client-side form management
 * 
 * SECURITY NOTES:
 * - All validation is also performed server-side
 * - No sensitive business logic exposed
 * - Input sanitization applied
 * - Rate limiting enforced server-side
 */

(function() {
    'use strict';
    
    // Security: Disable right-click context menu
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Security: Disable F12, Ctrl+Shift+I, Ctrl+U
    document.addEventListener('keydown', function(e) {
        if (e.keyCode === 123 || 
            (e.ctrlKey && e.shiftKey && e.keyCode === 73) ||
            (e.ctrlKey && e.keyCode === 85)) {
            e.preventDefault();
            return false;
        }
    });
    
    // Input sanitization function
    function sanitizeInput(input) {
        if (typeof input !== 'string') return input;
        
        return input
            .replace(/[<>]/g, '')
            .replace(/javascript:/gi, '')
            .replace(/vbscript:/gi, '')
            .replace(/on\w+\s*=/gi, '')
            .trim();
    }
    
    // Form validation helpers
    function validateEmail(email) {
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return emailRegex.test(email);
    }
    
    function validateRequired(value) {
        return value !== null && value !== undefined && value.toString().trim() !== '';
    }
    
    // Secure form submission
    function submitForm(formData, onSuccess, onError) {
        // Sanitize all string inputs
        const sanitizedData = {};
        for (let key in formData) {
            sanitizedData[key] = sanitizeInput(formData[key]);
        }
        
        fetch('/api/submit-onboarding', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(sanitizedData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.stripe_url) {
                onSuccess(data);
            } else {
                onError(data.message || 'Submission failed');
            }
        })
        .catch(error => {
            console.error('Form submission error:', error);
            onError('Network error. Please try again.');
        });
    }
    
    // Initialize form when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('onboardingForm');
        if (!form) return;
        
        const errorMessage = document.getElementById('errorMessage');
        const successMessage = document.getElementById('successMessage');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const submitButton = document.getElementById('submitButton');
        
        // File upload handlers with validation
        function setupFileUpload(inputId, infoId) {
            const fileInput = document.getElementById(inputId);
            const fileInfo = document.getElementById(infoId);
            
            if (!fileInput || !fileInfo) return;
            
            fileInput.addEventListener('change', function() {
                const files = this.files;
                if (files.length > 0) {
                    // Validate file types and sizes
                    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
                    const maxSize = 5 * 1024 * 1024; // 5MB
                    
                    let validFiles = [];
                    for (let file of files) {
                        if (allowedTypes.includes(file.type) && file.size <= maxSize) {
                            validFiles.push(file.name);
                        }
                    }
                    
                    if (validFiles.length > 0) {
                        fileInfo.textContent = `Selected: ${validFiles.join(', ')}`;
                        fileInfo.style.color = '#00e676';
                    } else {
                        fileInfo.textContent = 'Invalid file type or size. Please select PDF, JPG, or PNG files under 5MB.';
                        fileInfo.style.color = '#ff6b6b';
                        this.value = '';
                    }
                } else {
                    fileInfo.textContent = 'No file selected';
                    fileInfo.style.color = '#e0e0e0';
                }
            });
        }
        
        // Setup file uploads
        setupFileUpload('menu_upload', 'menuFileInfo');
        setupFileUpload('additional_docs', 'additionalDocsInfo');
        setupFileUpload('faq_upload', 'faqFileInfo');
        
        // Conditional field display logic
        function updateConditionalFields() {
            const deliveryPickup = document.querySelector('input[name="delivery_pickup"]:checked');
            const deliveryServices = document.getElementById('deliveryServices');
            const pickupOptions = document.getElementById('pickupOptions');
            
            if (deliveryServices) deliveryServices.classList.remove('show');
            if (pickupOptions) pickupOptions.classList.remove('show');
            
            if (deliveryPickup) {
                if (deliveryPickup.value === 'Delivery' || deliveryPickup.value === 'Both') {
                    if (deliveryServices) deliveryServices.classList.add('show');
                }
                if (deliveryPickup.value === 'Pickup' || deliveryPickup.value === 'Both') {
                    if (pickupOptions) pickupOptions.classList.add('show');
                }
            }
        }
        
        function updateLoginFields() {
            const selectedPlan = document.querySelector('input[name="plan"]:checked');
            const selectedMethod = document.querySelector('input[name="submission_method"]:checked');
            const loginSection = document.getElementById('loginSection');
            const proLoginSection = document.getElementById('proLoginSection');
            const sendSecurelyMessage = document.getElementById('sendSecurelyMessage');
            
            // Hide all conditional elements
            if (loginSection) loginSection.classList.remove('show');
            if (proLoginSection) proLoginSection.classList.remove('show');
            if (sendSecurelyMessage) sendSecurelyMessage.style.display = 'none';
            
            if (selectedPlan && selectedMethod) {
                if (selectedMethod.value === 'Submit through this page') {
                    if (loginSection) loginSection.classList.add('show');
                    
                    if (selectedPlan.value === 'Pro' && proLoginSection) {
                        proLoginSection.classList.add('show');
                    }
                } else if (selectedMethod.value === 'Use sendsecure.ly') {
                    if (sendSecurelyMessage) sendSecurelyMessage.style.display = 'block';
                }
            }
        }
        
        // Event listeners for conditional fields
        document.querySelectorAll('input[name="delivery_pickup"]').forEach(radio => {
            radio.addEventListener('change', updateConditionalFields);
        });
        
        document.querySelectorAll('input[name="plan"]').forEach(radio => {
            radio.addEventListener('change', updateLoginFields);
        });
        
        document.querySelectorAll('input[name="submission_method"]').forEach(radio => {
            radio.addEventListener('change', updateLoginFields);
        });
        
        // Check for pre-selected plan from URL
        const urlParams = new URLSearchParams(window.location.search);
        const plan = urlParams.get('plan');
        if (plan) {
            const planValue = plan === 'starter' ? 'Starter' : plan === 'pro' ? 'Pro' : null;
            if (planValue) {
                const planRadio = document.querySelector(`input[name="plan"][value="${planValue}"]`);
                if (planRadio) {
                    planRadio.checked = true;
                    updateLoginFields();
                }
            }
        }
        
        // Form submission handler
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (submitButton.disabled) return;
            
            // Show loading state
            if (loadingSpinner) loadingSpinner.style.display = 'block';
            if (errorMessage) errorMessage.style.display = 'none';
            if (successMessage) successMessage.style.display = 'none';
            submitButton.disabled = true;
            submitButton.textContent = 'Processing...';
            
            // Collect form data
            const formData = new FormData(form);
            const data = {};
            
            // Convert FormData to object with sanitization
            for (let [key, value] of formData.entries()) {
                if (key === 'delivery_services') {
                    if (!data.delivery_services) data.delivery_services = [];
                    data.delivery_services.push(sanitizeInput(value));
                } else {
                    data[key] = sanitizeInput(value);
                }
            }
            
            // Handle delivery_services array
            if (data.delivery_services) {
                data.delivery_services = data.delivery_services.join(', ');
            }
            
            // Add boolean fields
            data.confirm_accurate = document.getElementById('confirm_accurate')?.checked || false;
            data.consent_automation = document.getElementById('consent_automation')?.checked || false;
            data.consent_to_share = document.getElementById('consent_to_share')?.checked || false;
            
            // Client-side validation (server-side validation is the authority)
            const requiredFields = ['business_name', 'instagram_handle', 'business_type', 'contact_email'];
            for (let field of requiredFields) {
                if (!validateRequired(data[field])) {
                    showError(`${field.replace('_', ' ')} is required.`);
                    resetForm();
                    return;
                }
            }
            
            if (!validateEmail(data.contact_email)) {
                showError('Please enter a valid email address.');
                resetForm();
                return;
            }
            
            // Submit form
            submitForm(data, 
                function(response) {
                    if (successMessage) {
                        successMessage.style.display = 'block';
                        successMessage.textContent = response.message || 'Form submitted successfully!';
                    }
                    
                    // Redirect to Stripe after short delay
                    setTimeout(() => {
                        window.location.href = response.stripe_url;
                    }, 1500);
                },
                function(error) {
                    showError(error);
                    resetForm();
                }
            );
        });
        
        function showError(message) {
            if (errorMessage) {
                errorMessage.style.display = 'block';
                errorMessage.textContent = message;
            }
        }
        
        function resetForm() {
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            submitButton.disabled = false;
            submitButton.textContent = 'Start My Setup';
        }
        
        // Initialize conditional fields
        updateConditionalFields();
        updateLoginFields();
    });
})();