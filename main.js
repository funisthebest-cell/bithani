/* =====================================================
   빛한의원 - 공통 JavaScript
   ===================================================== */

document.addEventListener('DOMContentLoaded', function () {

  // ===================================================
  // 1. 네비게이션 스크롤 효과
  // ===================================================
  const navbar  = document.querySelector('.navbar');
  const hasHero = document.querySelector('.hero');

  function updateNavbar() {
    if (window.scrollY > 60) {
      navbar.classList.add('scrolled');
      navbar.classList.remove('hero-nav');
    } else {
      navbar.classList.remove('scrolled');
      if (hasHero) navbar.classList.add('hero-nav');
    }
  }

  if (hasHero) navbar.classList.add('hero-nav');
  window.addEventListener('scroll', updateNavbar, { passive: true });
  updateNavbar();

  // ===================================================
  // 2. 모바일 햄버거 메뉴
  // ===================================================
  const hamburger  = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', function () {
      const isOpen = mobileMenu.classList.toggle('open');
      hamburger.classList.toggle('active', isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    mobileMenu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        mobileMenu.classList.remove('open');
        hamburger.classList.remove('active');
        document.body.style.overflow = '';
      });
    });
  }

  // ===================================================
  // 3. 스크롤 페이드인 애니메이션
  // ===================================================
  const fadeEls = document.querySelectorAll('.fade-in');

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    fadeEls.forEach(function (el) { io.observe(el); });
  } else {
    // IntersectionObserver 미지원 브라우저 폴백
    fadeEls.forEach(function (el) { el.classList.add('visible'); });
  }

  // ===================================================
  // 4. 현재 페이지 네비 메뉴 활성화
  // ===================================================
  const page = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(function (link) {
    if (link.getAttribute('href') === page) {
      link.classList.add('active');
    }
  });

  // ===================================================
  // 5. 부드러운 스크롤 (앵커 링크)
  // ===================================================
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offset = 80;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top: top, behavior: 'smooth' });
      }
    });
  });

});
