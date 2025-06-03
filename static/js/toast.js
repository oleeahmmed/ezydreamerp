document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('.animate-fade-in > div');
    messages.forEach((message, index) => {
        setTimeout(() => {
            if (message.parentElement) {
                message.classList.add('opacity-0', 'scale-95');
                setTimeout(() => {
                    if (message.parentElement) {
                        message.remove();
                    }
                }, 300);
            }
        }, 5000 + (index * 500)); // Staggered dismissal
    });
});