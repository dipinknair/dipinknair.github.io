(function () {
  var siteRoot = new URL('../../', document.currentScript.src);
  document.getElementById('year').textContent = new Date().getFullYear();

  var themeToggle = document.getElementById('themeToggle');
  var moonIcon = document.getElementById('moonIcon');
  var sunIcon = document.getElementById('sunIcon');
  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
  try {
    var savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light' || savedTheme === 'dark') {
      document.documentElement.dataset.theme = savedTheme;
    }
  } catch (error) {
    console.warn('Unable to read the saved theme.', error);
  }

  function isDark() {
    var theme = document.documentElement.dataset.theme;
    return theme ? theme === 'dark' : prefersDark.matches;
  }
  function updateThemeToggle() {
    moonIcon.toggleAttribute('hidden', isDark());
    sunIcon.toggleAttribute('hidden', !isDark());
    themeToggle.setAttribute('aria-label', 'Switch to ' + (isDark() ? 'light' : 'dark') + ' theme');
  }
  themeToggle.addEventListener('click', function () {
    var theme = isDark() ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem('theme', theme);
    } catch (error) {
      console.warn('Unable to save the selected theme.', error);
    }
    updateThemeToggle();
  });
  prefersDark.addEventListener('change', updateThemeToggle);
  updateThemeToggle();

  var q = document.getElementById('q');
  var results = document.getElementById('results');
  var pages = window.siteSearchPages;
  if (!Array.isArray(pages)) {
    console.error('The site search index could not be loaded.');
    q.disabled = true;
    q.placeholder = 'Search unavailable';
    return;
  }

  function snippet(p, term) {
    var text = p.text;
    var lower = text.toLowerCase();
    var titleIndex = lower.indexOf(p.title.toLowerCase());
    var i = lower.indexOf(term, titleIndex < 0 ? 0 : titleIndex + p.title.length);
    if (i < 0) i = lower.indexOf(term);
    var start = Math.max(0, i - 50);
    var span = document.createElement('span');
    span.append((start ? '\u2026' : '') + text.slice(start, i));
    var mark = document.createElement('mark');
    mark.textContent = text.slice(i, i + term.length);
    span.append(mark);
    span.append(text.slice(i + term.length, i + term.length + 70) + '\u2026');
    return span;
  }
  function search() {
    var terms = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    results.textContent = '';
    if (!terms.length) {
      results.hidden = true;
      return;
    }
    var hits = pages.map(function (p) {
      var text = p.text.toLowerCase();
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var count = text.split(terms[i]).length - 1;
        if (!count) return null;
        score += count;
      }
      return {page: p, score: score};
    }).filter(Boolean).sort(function (a, b) {
      return b.score - a.score;
    }).slice(0, 6);
    hits.forEach(function (hit) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      var title = document.createElement('b');
      a.href = new URL(hit.page.url, siteRoot).href;
      title.textContent = hit.page.title;
      a.append(title, snippet(hit.page, terms[0]));
      li.append(a);
      results.append(li);
    });
    if (!hits.length) {
      var li = document.createElement('li');
      li.className = 'none';
      li.textContent = 'No matches';
      results.append(li);
    }
    results.hidden = false;
  }
  function closeSearch() {
    q.value = '';
    results.hidden = true;
  }
  q.addEventListener('input', search);
  q.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeSearch();
    if (event.key === 'Enter') {
      var first = results.querySelector('a');
      if (first) {
        event.preventDefault();
        location.href = first.href;
        closeSearch();
        q.blur();
      }
    }
  });
  results.addEventListener('click', function (event) {
    if (event.target.closest('a')) closeSearch();
  });
  document.addEventListener('click', function (event) {
    if (!event.target.closest('.search')) results.hidden = true;
  });
})();
