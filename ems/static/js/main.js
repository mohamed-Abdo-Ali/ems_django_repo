    // Password Strength Indicator
    document.querySelector('input[type="password"]').addEventListener('input', function() {
        const strengthBar = document.getElementById('password-strength');
        const length = this.value.length;
        
        if (length === 0) {
            strengthBar.style.width = '0%';
            strengthBar.className = 'h-full bg-gray-500 w-0 transition-all duration-300';
        } else if (length < 4) {
            strengthBar.style.width = '25%';
            strengthBar.className = 'h-full bg-red-500 transition-all duration-300';
        } else if (length < 8) {
            strengthBar.style.width = '50%';
            strengthBar.className = 'h-full bg-yellow-500 transition-all duration-300';
        } else {
            strengthBar.style.width = '100%';
            strengthBar.className = 'h-full bg-green-500 transition-all duration-300';
        }
    });

    // Toggle Password Visibility
    document.getElementById('toggle-password').addEventListener('click', function() {
        const passwordField = document.querySelector('input[type="password"]');
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            this.classList.remove('fa-eye');
            this.classList.add('fa-eye-slash');
        } else {
            passwordField.type = 'password';
            this.classList.remove('fa-eye-slash');
            this.classList.add('fa-eye');
        }
    });