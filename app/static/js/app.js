// ============================================
// DATING APP - MAIN JAVASCRIPT (STABLE VERSION)
// ============================================

document.addEventListener('DOMContentLoaded', function () {

    // ==============================
    // UNREAD MESSAGE COUNT
    // ==============================
    updateUnreadCount();
    setInterval(updateUnreadCount, 30000);

    // ==============================
    // AUTO HIDE FLASH MESSAGES
    // ==============================
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(msg => {
            msg.style.opacity = '0';
            msg.style.transition = 'opacity 0.5s';
            setTimeout(() => msg.remove(), 500);
        });
    }, 5000);

    // ==============================
    // CHAT UNSENT MESSAGE PROTECTION (FIXED)
    // ==============================
    let hasUnsentMessage = false;
    const messageInput = document.getElementById('messageInput');
    const chatForm = document.querySelector('.chat-form');

    if (messageInput) {
        messageInput.addEventListener('input', function () {
            hasUnsentMessage = this.value.trim().length > 0;
        });
    }

    if (chatForm) {
        chatForm.addEventListener('submit', function () {
            // Reset flag when message is actually sent
            hasUnsentMessage = false;
        });
    }

    window.addEventListener('beforeunload', function (e) {
        if (hasUnsentMessage) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    // ==============================
    // IMAGE PREVIEW
    // ==============================
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            const preview = e.target.parentElement.querySelector('.photo-preview');

            reader.onload = function (event) {
                if (preview) {
                    preview.src = event.target.result;
                } else {
                    const img = document.createElement('img');
                    img.src = event.target.result;
                    img.className = 'photo-preview';
                    e.target.parentElement.insertBefore(img, e.target);
                }
            };

            reader.readAsDataURL(file);
        });
    });

    // ==============================
    // FORM VALIDATION
    // ==============================
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function (e) {

            // Skip validation for chat form
            if (form.classList.contains('chat-form')) return;

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

    // ==============================
    // AGE VALIDATION
    // ==============================
    const ageInput = document.getElementById('age');
    if (ageInput) {
        ageInput.addEventListener('change', function () {
            const age = parseInt(this.value);
            if (age < 18) {
                alert('You must be at least 18 years old to use this app.');
                this.value = 18;
            }
        });
    }

    // ==============================
    // AGE RANGE VALIDATION
    // ==============================
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

    // ==============================
    // MOBILE MENU TOGGLE
    // ==============================
    const menuToggle = document.querySelector('.menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function () {
            document.querySelector('.nav-links').classList.toggle('active');
        });
    }

    // ==============================
    // LAZY LOAD IMAGES
    // ==============================
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

});


// ============================================
// UNREAD COUNT FUNCTION
// ============================================

async function updateUnreadCount() {
    try {
        const response = await fetch('/messages/unread-count');
        const data = await response.json();

        const badge = document.getElementById('unread-badge');
        if (!badge) return;

        if (data.count > 0) {
            badge.textContent = data.count > 99 ? '99+' : data.count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }

    } catch (error) {
        console.error('Error updating unread count:', error);
    }
}
