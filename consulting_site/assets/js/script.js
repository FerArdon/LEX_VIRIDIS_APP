// Navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
});

// Mobile hamburger
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('navLinks');

hamburger.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    const bars = hamburger.querySelectorAll('.bar');
    bars[0].style.transform = navLinks.classList.contains('open') ? 'rotate(45deg) translate(5px,5px)'   : '';
    bars[1].style.opacity   = navLinks.classList.contains('open') ? '0' : '1';
    bars[2].style.transform = navLinks.classList.contains('open') ? 'rotate(-45deg) translate(5px,-5px)' : '';
});

// Close menu on link click
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        navLinks.classList.remove('open');
        hamburger.querySelectorAll('.bar').forEach(b => { b.style.transform = ''; b.style.opacity = ''; });
    });
});

// Active nav link on scroll
const sections = document.querySelectorAll('section[id], header[id]');
const navItems = document.querySelectorAll('.nav-links a[href^="#"]');

const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            navItems.forEach(a => a.classList.remove('active'));
            const active = document.querySelector(`.nav-links a[href="#${entry.target.id}"]`);
            if (active) active.classList.add('active');
        }
    });
}, { threshold: 0.4 });

sections.forEach(s => observer.observe(s));

// Contact form — opens mailto
document.getElementById('contactForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const name    = document.getElementById('name').value.trim();
    const email   = document.getElementById('email').value.trim();
    const subject = document.getElementById('subject').value.trim() || 'Consulta desde sedcaf.com';
    const message = document.getElementById('message').value.trim();

    const body = encodeURIComponent(
        `Nombre: ${name}\nCorreo: ${email}\n\n${message}`
    );

    window.location.href = `mailto:frardonr@hotmail.com?subject=${encodeURIComponent(subject)}&body=${body}`;

    document.getElementById('formNote').textContent = '¡Gracias! Se abrirá su cliente de correo.';
    this.reset();
});
