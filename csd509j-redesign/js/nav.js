/* ============================================================
   nav.js — Header navigation, mobile drawer, breadcrumb,
             active link detection
   CSD 509J School District
   ============================================================ */
(function () {
  'use strict';

  /* ---- Cache DOM elements ---- */
  var hamburger    = document.querySelector('.site-nav__hamburger');
  var mobileNav    = document.querySelector('.mobile-nav');
  var overlay      = document.querySelector('.mobile-overlay');
  var siteNav      = document.querySelector('.site-nav');
  var breadcrumb   = document.querySelector('.breadcrumb');
  var navLinks     = document.querySelectorAll('.site-nav__links a');

  /* ---- Mobile drawer helpers ---- */
  function openDrawer() {
    if (!mobileNav || !overlay) return;
    mobileNav.classList.add('open');
    overlay.classList.add('visible');
    document.body.style.overflow = 'hidden';
    if (hamburger) hamburger.setAttribute('aria-expanded', 'true');
  }

  function closeDrawer() {
    if (!mobileNav || !overlay) return;
    mobileNav.classList.remove('open');
    overlay.classList.remove('visible');
    document.body.style.overflow = '';
    if (hamburger) hamburger.setAttribute('aria-expanded', 'false');
  }

  function isDrawerOpen() {
    return mobileNav && mobileNav.classList.contains('open');
  }

  /* ---- Hamburger toggle ---- */
  if (hamburger) {
    hamburger.addEventListener('click', function () {
      if (isDrawerOpen()) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });
  }

  /* ---- Overlay click closes drawer ---- */
  if (overlay) {
    overlay.addEventListener('click', function () {
      closeDrawer();
    });
  }

  /* ---- Escape key closes drawer ---- */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isDrawerOpen()) {
      closeDrawer();
    }
  });

  /* ---- Clicking a link inside mobile nav closes drawer ---- */
  if (mobileNav) {
    var mobileLinks = mobileNav.querySelectorAll('a');
    for (var i = 0; i < mobileLinks.length; i++) {
      mobileLinks[i].addEventListener('click', function () {
        closeDrawer();
      });
    }
  }

  /* ============================================================
     Active link detection
     ============================================================ */
  var currentPath = window.location.pathname;

  /* Normalise trailing slash for comparison */
  function normalisePath(p) {
    if (p !== '/' && p.charAt(p.length - 1) !== '/') {
      return p + '/';
    }
    return p;
  }

  var normCurrent = normalisePath(currentPath);

  for (var j = 0; j < navLinks.length; j++) {
    var linkHref = navLinks[j].getAttribute('href');
    if (!linkHref) continue;

    /* Resolve relative href against document base */
    var resolved;
    try {
      resolved = new URL(linkHref, window.location.href).pathname;
    } catch (e) {
      resolved = linkHref;
    }

    var normLink = normalisePath(resolved);

    if (normCurrent === normLink) {
      navLinks[j].classList.add('active');
    } else if (normCurrent.indexOf(normLink) === 0 && normLink !== normalisePath('/csd509j-redesign/')) {
      /* Sub-page match: e.g. /about/team/ matches /about/ */
      navLinks[j].classList.add('active');
    }
  }

  /* ============================================================
     Breadcrumb generation
     ============================================================ */
  if (breadcrumb) {
    var basePath = '/csd509j-redesign/';
    var relativePath = currentPath;

    /* Strip the base path prefix */
    if (relativePath.indexOf(basePath) === 0) {
      relativePath = relativePath.substring(basePath.length);
    }

    /* Remove leading/trailing slashes, split */
    relativePath = relativePath.replace(/^\/+|\/+$/g, '');
    var segments = relativePath ? relativePath.split('/') : [];

    /* Build crumb list */
    var crumbs = [];
    crumbs.push({ label: 'Home', href: basePath });

    var accumulated = basePath;
    for (var k = 0; k < segments.length; k++) {
      accumulated += segments[k] + '/';
      var label = segments[k]
        .replace(/-/g, ' ')
        .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
      crumbs.push({
        label: label,
        href: (k === segments.length - 1) ? '' : accumulated
      });
    }

    /* Render */
    var frag = document.createDocumentFragment();
    for (var m = 0; m < crumbs.length; m++) {
      var li = document.createElement('li');
      li.className = 'breadcrumb__item';

      if (crumbs[m].href && m < crumbs.length - 1) {
        var a = document.createElement('a');
        a.href = crumbs[m].href;
        a.textContent = crumbs[m].label;
        li.appendChild(a);
      } else {
        var span = document.createElement('span');
        span.textContent = crumbs[m].label;
        span.setAttribute('aria-current', 'page');
        li.appendChild(span);
      }

      frag.appendChild(li);
    }

    breadcrumb.innerHTML = '';
    breadcrumb.appendChild(frag);
  }

  /* ============================================================
     Sticky nav — no opacity change needed (solid white bg now)
     ============================================================ */
})();
