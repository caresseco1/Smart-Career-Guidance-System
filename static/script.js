// Smooth Scrolling for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Open and close modals
const loginBtn = document.getElementById('loginBtn');
const signupBtn = document.getElementById('signupBtn');
const loginModal = document.getElementById('loginModal');
const signupModal = document.getElementById('signupModal');
const closeBtns = document.querySelectorAll('.close');

loginBtn.addEventListener('click', () => {
    loginModal.style.display = 'flex';
});

signupBtn.addEventListener('click', () => {
    signupModal.style.display = 'flex';
});

closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        loginModal.style.display = 'none';
        signupModal.style.display = 'none';
    });
});
