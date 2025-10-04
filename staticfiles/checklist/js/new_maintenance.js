document.addEventListener('DOMContentLoaded', function() {
    // File upload preview
    const fileInput = document.getElementById(attachmentFieldId);
    const filePreview = document.getElementById('filePreview');
    const fileList = document.getElementById('fileList');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            fileList.innerHTML = '';
            
            if (this.files.length > 0) {
                filePreview.style.display = 'block';
                
                for (let i = 0; i < this.files.length; i++) {
                    const file = this.files[i];
                    const listItem = document.createElement('li');
                    listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    listItem.innerHTML = `
                        <div>
                            <i class="fas fa-file me-2"></i> ${file.name}
                            <small class="text-muted ms-2">(${(file.size / 1024 / 1024).toFixed(2)} MB)</small>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-danger remove-file" data-index="${i}">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                    fileList.appendChild(listItem);
                }
                
                // Add event listeners to remove buttons
                document.querySelectorAll('.remove-file').forEach(button => {
                    button.addEventListener('click', function() {
                        const index = parseInt(this.getAttribute('data-index'));
                        removeFile(index);
                    });
                });
            } else {
                filePreview.style.display = 'none';
            }
        });
    }
    
    function removeFile(index) {
        // Create a new FileList without the removed file
        const dt = new DataTransfer();
        const files = fileInput.files;
        
        for (let i = 0; i < files.length; i++) {
            if (i !== index) {
                dt.items.add(files[i]);
            }
        }
        
        fileInput.files = dt.files;
        
        // Trigger change event to update preview
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    }
    
    // Due date validation - must be after today
    const dueDateField = document.getElementById(dueDateFieldId);
    if (dueDateField) {
        dueDateField.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate < today) {
                alert('Due date cannot be in the past. Please select a future date.');
                this.value = '';
            }
        });
    }
    
    // Form submission handling
    const form = document.getElementById('maintenanceForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Add any additional validation here if needed
            const submitButton = e.submitter;
            
            if (submitButton.name === 'submit') {
                // Validate required fields for final submission
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;
                
                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        isValid = false;
                        field.classList.add('is-invalid');
                    } else {
                        field.classList.remove('is-invalid');
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    alert('Please fill in all required fields before submitting the ticket.');
                }
            }
        });
    }
});