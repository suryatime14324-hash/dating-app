// Dating App - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Update unread message count
    updateUnreadCount();
    
    // Poll for unread messages every 30 seconds
    setInterval(updateUnreadCount, 30000);
    
    // Auto-hide flash messages
    setTimeout(() => {
        const flashMessages = document.querySelectorAll('.alert');
        flashMessages.forEach(msg => {
            msg.style.opacity = '0';
            msg.style.transition = 'opacity 0.5s';
            setTimeout(() => msg.remove(), 500);
        });
    }, 5000);
});

// Update unread message count
async function updateUnreadCount() {
    try {
        const response = await fetch('/messages/unread-count');
        const data = await response.json();
        
        const badge = document.getElementById('unread-badge');
        if (badge) {
            if (data.count > 0) {
                badge.textContent = data.count > 99 ? '99+' : data.count;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error updating unread count:', error);
    }
}

// Image preview for file uploads
document.querySelectorAll('input[type="file"]').forEach(input => {
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            const preview = e.target.parentElement.querySelector('.photo-preview');
            
            reader.onload = function(e) {
                if (preview) {
                    preview.src = e.target.result;
                } else {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'photo-preview';
                    e.target.parentElement.insertBefore(img, e.target);
                }
            };
            
            reader.readAsDataURL(file);
        }
    });
});

// Form validation
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.style.borderColor = '#ff4757';
            } else {
                field.style.borderColor = '';
            }
        });
        
        if (!isValid) {
            e.preventDefault();
        }
    });
});

// Age validation
const ageInput = document.getElementById('age');
if (ageInput) {
    ageInput.addEventListener('change', function() {
        const age = parseInt(this.value);
        if (age < 18) {
            alert('You must be at least 18 years old to use this app.');
            this.value = 18;
        }
    });
}

// Preference validation (min age < max age)
const minAgeInput = document.getElementById('min_age');
const maxAgeInput = document.getElementById('max_age');

if (minAgeInput && maxAgeInput) {
    function validateAgeRange() {
        const min = parseInt(minAgeInput.value) || 18;
        const max = parseInt(maxAgeInput.value) || 99;
        
        if (min > max) {
            maxAgeInput.value = min;
        }
    }
    
    minAgeInput.addEventListener('change', validateAgeRange);
    maxAgeInput.addEventListener('change', validateAgeRange);
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Mobile menu toggle (if needed)
const menuToggle = document.querySelector('.menu-toggle');
if (menuToggle) {
    menuToggle.addEventListener('click', function() {
        document.querySelector('.nav-links').classList.toggle('active');
    });
}

// Confirm before leaving chat with unsent message
let hasUnsentMessage = false;
const messageInput = document.getElementById('messageInput');
if (messageInput) {
    messageInput.addEventListener('input', function() {
        hasUnsentMessage = this.value.trim().length > 0;
    });
    
    window.addEventListener('beforeunload', function(e) {
        if (hasUnsentMessage) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Lazy load images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img.lazy').forEach(img => {
        imageObserver.observe(img);
    });
}
