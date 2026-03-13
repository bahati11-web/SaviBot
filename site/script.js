document.querySelectorAll('.glass').forEach(el => {
  el.style.opacity = 0;
  el.style.transform = "translateY(20px)";
});

window.addEventListener('scroll', () => {
  document.querySelectorAll('.glass').forEach(el => {
    const rect = el.getBoundingClientRect();
    if(rect.top < window.innerHeight - 50) {
      el.style.transition = "all 0.8s ease-out";
      el.style.opacity = 1;
      el.style.transform = "translateY(0)";
    }
  });
});
