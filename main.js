const backToTop = document.querySelector('.back-to-top');

document.addEventListener('scroll', function () {
  if (window.scrollY > 500) {
    backToTop.style.display = 'inline-block';
  } else {
    backToTop.style.display = 'none';
  }
});

backToTop.addEventListener('click', () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  });
});
