/* ============================================================
   main.js — Scroll reveal, counter animation, alert dismiss,
              accordion, progress bar, sticky nav
   CSD 509J School District
   ============================================================ */
(function () {
  'use strict';

  /* ---- Reduced motion preference ---- */
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ============================================================
     Scroll Reveal
     ============================================================ */
  var revealElements = document.querySelectorAll('.reveal');

  if (prefersReducedMotion) {
    /* Immediately show all reveal elements — no animation */
    for (var r = 0; r < revealElements.length; r++) {
      revealElements[r].classList.add('visible');
    }
  } else {
    /* Immediately reveal hero elements on page load (homepage + inner pages) */
    var heroReveals = document.querySelectorAll('.hero .reveal, .hero.reveal, .page-hero .reveal, .page-hero.reveal');
    for (var h = 0; h < heroReveals.length; h++) {
      heroReveals[h].classList.add('visible');
    }

    /* IntersectionObserver for remaining reveals */
    if ('IntersectionObserver' in window) {
      var revealObserver = new IntersectionObserver(function (entries) {
        for (var i = 0; i < entries.length; i++) {
          if (entries[i].isIntersecting) {
            entries[i].target.classList.add('visible');
            revealObserver.unobserve(entries[i].target);
          }
        }
      }, {
        threshold: 0.08,
        rootMargin: '0px 0px -20px 0px'
      });

      for (var v = 0; v < revealElements.length; v++) {
        if (!revealElements[v].classList.contains('visible')) {
          revealObserver.observe(revealElements[v]);
        }
      }
    } else {
      /* Fallback: show everything if IO not supported */
      for (var f = 0; f < revealElements.length; f++) {
        revealElements[f].classList.add('visible');
      }
    }
  }

  /* ============================================================
     Counter Animation
     ============================================================ */
  var counters = document.querySelectorAll('[data-counter]');

  function animateCounter(el) {
    var target   = parseInt(el.getAttribute('data-counter'), 10) || 0;
    var prefix   = el.getAttribute('data-prefix') || '';
    var suffix   = el.getAttribute('data-suffix') || '';
    var duration = 2000;
    var start    = null;

    if (prefersReducedMotion) {
      el.textContent = prefix + target.toLocaleString() + suffix;
      return;
    }

    function step(timestamp) {
      if (!start) start = timestamp;
      var elapsed  = timestamp - start;
      var progress = Math.min(elapsed / duration, 1);

      /* Ease-out cubic: 1 - (1 - t)^3 */
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = Math.round(eased * target);

      el.textContent = prefix + current.toLocaleString() + suffix;

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = prefix + target.toLocaleString() + suffix;
      }
    }

    requestAnimationFrame(step);
  }

  if (counters.length > 0 && 'IntersectionObserver' in window) {
    var counterObserver = new IntersectionObserver(function (entries) {
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].isIntersecting) {
          animateCounter(entries[i].target);
          counterObserver.unobserve(entries[i].target);
        }
      }
    }, { threshold: 0.2 });

    for (var c = 0; c < counters.length; c++) {
      counterObserver.observe(counters[c]);
    }
  } else {
    /* Fallback or reduced motion: set final values immediately */
    for (var cf = 0; cf < counters.length; cf++) {
      var t = parseInt(counters[cf].getAttribute('data-counter'), 10) || 0;
      var p = counters[cf].getAttribute('data-prefix') || '';
      var s = counters[cf].getAttribute('data-suffix') || '';
      counters[cf].textContent = p + t.toLocaleString() + s;
    }
  }

  /* ============================================================
     Alert Banner Dismiss
     ============================================================ */
  var ALERT_KEY   = 'alert-dismissed';
  var alertBanner = document.querySelector('.alert-banner');
  var alertClose  = document.querySelector('.alert-banner__close');

  if (alertBanner) {
    if (localStorage.getItem(ALERT_KEY)) {
      alertBanner.style.display = 'none';
    } else if (alertClose) {
      alertClose.addEventListener('click', function () {
        alertBanner.style.display = 'none';
        localStorage.setItem(ALERT_KEY, 'true');
      });
    }
  }

  /* ============================================================
     Accordion — one-at-a-time within each .accordion parent
     ============================================================ */
  var accordions = document.querySelectorAll('.accordion');

  for (var a = 0; a < accordions.length; a++) {
    (function (accordion) {
      var details = accordion.querySelectorAll('details');

      for (var d = 0; d < details.length; d++) {
        details[d].addEventListener('toggle', function () {
          if (!this.open) return;
          var siblings = accordion.querySelectorAll('details');
          var current  = this;
          for (var s = 0; s < siblings.length; s++) {
            if (siblings[s] !== current && siblings[s].open) {
              siblings[s].removeAttribute('open');
            }
          }
        });
      }
    })(accordions[a]);
  }

  /* ============================================================
     Progress Bar
     ============================================================ */
  var progressBar = document.querySelector('.progress-bar');

  if (progressBar) {
    var progressTicking = false;

    function updateProgressBar() {
      var scrollTop    = window.pageYOffset || document.documentElement.scrollTop;
      var docHeight    = document.documentElement.scrollHeight;
      var clientHeight = document.documentElement.clientHeight;
      var scrollable   = docHeight - clientHeight;
      var percent      = scrollable > 0 ? (scrollTop / scrollable) * 100 : 0;
      progressBar.style.width = percent + '%';
      progressTicking = false;
    }

    window.addEventListener('scroll', function () {
      if (!progressTicking) {
        requestAnimationFrame(updateProgressBar);
        progressTicking = true;
      }
    }, { passive: true });

    /* Set initial state */
    updateProgressBar();
  }

  /* ============================================================
     Sticky Nav — no opacity change needed (solid white bg now)
     ============================================================ */
})();
