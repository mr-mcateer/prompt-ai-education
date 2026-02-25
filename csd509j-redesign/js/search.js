/* ============================================================
   search.js — Cmd/Ctrl+K search overlay with client-side
                fuzzy matching against a static index
   CSD 509J School District
   ============================================================
   ✎ CUSTOMIZATION: Update the SEARCH_INDEX array below to match
   your district's schools, departments, and pages. Each entry
   needs three fields:
     - name:    what the user types to find it
     - section: category label shown in search results
     - href:    relative URL to the page (from site root)
   ============================================================ */
(function () {
  'use strict';

  /* ---- Search index — ✎ Edit these entries for your district ---- */
  var SEARCH_INDEX = [
    { name: 'About', section: 'District', href: 'about/' },
    { name: 'Leadership', section: 'District', href: 'about/#leadership' },
    { name: 'Strategic Path', section: 'District', href: 'about/#strategic' },
    { name: 'Schools Directory', section: 'Schools', href: 'schools/' },
    { name: 'Adams Elementary', section: 'Schools', href: 'schools/#adams' },
    { name: 'Garfield Elementary', section: 'Schools', href: 'schools/#garfield' },
    { name: 'Hoover Elementary', section: 'Schools', href: 'schools/#hoover' },
    { name: 'Jefferson Elementary', section: 'Schools', href: 'schools/#jefferson' },
    { name: 'Lincoln Elementary', section: 'Schools', href: 'schools/#lincoln' },
    { name: 'Muddy Creek Charter', section: 'Schools', href: 'schools/#muddy-creek' },
    { name: 'Wilson Elementary', section: 'Schools', href: 'schools/#wilson' },
    { name: 'College Hill (K-8)', section: 'Schools', href: 'schools/#college-hill' },
    { name: 'Cheldelin Middle School', section: 'Schools', href: 'schools/#cheldelin' },
    { name: 'Linus Pauling Middle School', section: 'Schools', href: 'schools/#linus-pauling' },
    { name: 'Corvallis High School', section: 'Schools', href: 'schools/#corvallis-high' },
    { name: 'Crescent Valley High School', section: 'Schools', href: 'schools/#crescent-valley' },
    { name: 'Letitia Carson Elementary', section: 'Schools', href: 'schools/#letitia-carson' },
    { name: 'Bridges (Alternative Programs)', section: 'Schools', href: 'schools/#bridges' },
    { name: 'Enrollment & Registration', section: 'Families', href: 'families/#enrollment' },
    { name: 'Transportation & Bus Routes', section: 'Families', href: 'families/#transportation' },
    { name: 'School Menus', section: 'Families', href: 'families/#menus' },
    { name: 'School Safety', section: 'Families', href: 'families/#safety' },
    { name: 'Special Education & Multilingual', section: 'Families', href: 'families/#special-ed' },
    { name: 'School Board', section: 'Community', href: 'community/#board' },
    { name: 'Employment Opportunities', section: 'Community', href: 'community/#employment' },
    { name: 'School Calendar', section: 'Community', href: 'community/#calendar' },
    { name: 'Staff Resources', section: 'Staff', href: 'staff/' },
    { name: 'ClassLink', section: 'Staff', href: 'staff/#classlink' },
    { name: 'Contracts & Salary', section: 'Staff', href: 'staff/#contracts' },
    { name: 'Employee Benefits', section: 'Staff', href: 'staff/#benefits' },
    { name: 'IT Support', section: 'Staff', href: 'staff/#it' },
    { name: 'Business Services', section: 'Departments', href: 'departments/#business' },
    { name: 'Human Resources', section: 'Departments', href: 'departments/#hr' },
    { name: 'Technology Services', section: 'Departments', href: 'departments/#tech' },
    { name: 'Facilities & Maintenance', section: 'Departments', href: 'departments/#facilities' },
    { name: 'Food & Nutrition', section: 'Departments', href: 'departments/#food' },
    { name: 'Student Transportation', section: 'Departments', href: 'departments/#transportation' },
    { name: 'Equity & Community Engagement', section: 'Departments', href: 'departments/#equity' },
    { name: 'Communications', section: 'Departments', href: 'departments/#communications' },
    { name: 'Student Growth & Experience', section: 'Departments', href: 'departments/#student-growth' },
    { name: 'Contact Us', section: 'Contact', href: 'contact/' },
    { name: 'News & Announcements', section: 'News', href: 'news/' }
  ];

  var MAX_RESULTS = 12;

  /* ---- Cache DOM ---- */
  var searchOverlay = document.querySelector('.search-overlay');
  var searchInput   = searchOverlay ? searchOverlay.querySelector('input') : null;
  var resultsBox    = searchOverlay ? searchOverlay.querySelector('.search-overlay__results') : null;

  if (!searchOverlay || !searchInput || !resultsBox) return;

  /* ---- Helpers ---- */
  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function getBasePath() {
    var base = '/csd509j-redesign/';
    var path = window.location.pathname;

    /* If we are already under the base, compute relative prefix */
    if (path.indexOf(base) === 0) {
      var rest = path.substring(base.length).replace(/\/+$/, '');
      var depth = rest ? rest.split('/').length : 0;
      var prefix = '';
      for (var i = 0; i < depth; i++) {
        prefix += '../';
      }
      return prefix || './';
    }

    /* Fallback: use absolute base */
    return base;
  }

  function highlightMatch(text, query) {
    if (!query) return escapeHtml(text);
    var escaped = escapeHtml(text);
    var idx = escaped.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return escaped;
    var before = escaped.substring(0, idx);
    var match  = escaped.substring(idx, idx + query.length);
    var after  = escaped.substring(idx + query.length);
    return before + '<mark>' + match + '</mark>' + after;
  }

  /* ---- Open / Close ---- */
  function openSearch() {
    searchOverlay.classList.add('open');
    searchInput.value = '';
    resultsBox.innerHTML = '';
    searchInput.focus();
  }

  function closeSearch() {
    searchOverlay.classList.remove('open');
    searchInput.value = '';
    resultsBox.innerHTML = '';
  }

  /* ---- Keyboard shortcut: Cmd/Ctrl + K ---- */
  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (searchOverlay.classList.contains('open')) {
        closeSearch();
      } else {
        openSearch();
      }
    }

    if (e.key === 'Escape' && searchOverlay.classList.contains('open')) {
      closeSearch();
    }
  });

  /* ---- Clicking overlay background closes ---- */
  searchOverlay.addEventListener('click', function (e) {
    if (e.target === searchOverlay) {
      closeSearch();
    }
  });

  /* ---- Search logic with debounce ---- */
  var debounceTimer = null;

  searchInput.addEventListener('keyup', function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runSearch, 120);
  });

  function runSearch() {
    var query = searchInput.value.trim();
    resultsBox.innerHTML = '';

    if (!query) return;

    var lowerQuery = query.toLowerCase();
    var matches = [];

    for (var i = 0; i < SEARCH_INDEX.length; i++) {
      var entry = SEARCH_INDEX[i];
      var nameMatch    = entry.name.toLowerCase().indexOf(lowerQuery) !== -1;
      var sectionMatch = entry.section.toLowerCase().indexOf(lowerQuery) !== -1;

      if (nameMatch || sectionMatch) {
        matches.push(entry);
      }
      if (matches.length >= MAX_RESULTS) break;
    }

    if (matches.length === 0) {
      var empty = document.createElement('div');
      empty.className = 'search-result search-result--empty';
      empty.style.color = '#888';
      empty.style.padding = '1rem';
      empty.textContent = 'No results found';
      resultsBox.appendChild(empty);
      return;
    }

    var basePath = getBasePath();
    var frag = document.createDocumentFragment();

    for (var j = 0; j < matches.length; j++) {
      var item = matches[j];
      var link = document.createElement('a');
      link.className = 'search-result';
      link.href = basePath + item.href;

      var cat = document.createElement('span');
      cat.className = 'search-result__category';
      cat.textContent = item.section;

      var title = document.createElement('span');
      title.className = 'search-result__title';
      title.innerHTML = highlightMatch(item.name, query);

      link.appendChild(cat);
      link.appendChild(title);
      frag.appendChild(link);
    }

    resultsBox.appendChild(frag);
  }
})();
