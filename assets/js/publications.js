(function () {
  'use strict';

  var containers = document.querySelectorAll('[data-publications]');
  if (!containers.length) return;

  fetch('assets/data/publications.bib')
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.text();
    })
    .then(function (bib) {
      var publications = parseBibTeX(bib).sort(function (a, b) {
        return arxivSortKey(b.arxiv) - arxivSortKey(a.arxiv);
      });
      containers.forEach(function (container) { container.innerHTML = render(publications); });
    })
    .catch(function () {
      containers.forEach(function (container) {
        container.innerHTML = '<p class="publication-error">Unable to load publications.</p>';
      });
    });

  function parseBibTeX(text) {
    return text.split(/@\w+\s*\{/).slice(1).map(function (entry) {
      var fields = {};
      entry.replace(/([a-zA-Z_]+)\s*=\s*\{([^{}]*)\}|([a-zA-Z_]+)\s*=\s*"([^"]*)"/g, function (_, k1, v1, k2, v2) {
        fields[(k1 || k2).toLowerCase()] = (v1 || v2).trim();
        return _;
      });
      return fields;
    }).filter(function (item) { return item.title; });
  }

  function escapeHtml(value) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(value || ''));
    return div.innerHTML;
  }

  // arXiv identifiers begin with YYMM, which provides the requested
  // submission-time ordering without relying on journal publication dates.
  function arxivSortKey(value) {
    var match = String(value || '').match(/^(\d{2})(\d{2})\.(\d+)/);
    return match ? Number(match[1] + match[2] + match[3].padStart(6, '0')) : 0;
  }

  function authors(value) {
    return value.split(/\s+and\s+/i).map(function (author) {
      var parts = author.split(',').map(function (part) { return part.trim(); });
      return parts.length > 1 ? parts[1] + ' ' + parts[0] : parts[0];
    }).map(function (author) {
      return /^Yifei Wang$/i.test(author) ? '<b>Yifei Wang</b>' : escapeHtml(author);
    }).join(', ');
  }

  function render(items) {
    return '<ol class="pub-list">' + items.map(function (item) {
      var links = '<a href="https://arxiv.org/abs/' + encodeURIComponent(item.arxiv) + '" class="list-link" target="_blank" rel="noopener">arXiv</a>';
      if (item.journal_url && item.journal && !/^arXiv preprint/i.test(item.journal)) {
        links += '<span class="pub-sep"> · </span><a href="' + escapeHtml(item.journal_url) + '" class="list-link" target="_blank" rel="noopener">Journal</a>';
      }
      var venue = item.journal + (item.volume ? ', ' + item.volume : '') + (item.number ? '(' + item.number + ')' : '') + (item.pages ? ', ' + item.pages : '') + ' (' + item.year + ')';
      return '<li class="list-item"><span class="list-title">' + escapeHtml(item.title) + '</span><div class="list-meta">' + authors(item.author) + ' — <i>' + escapeHtml(venue) + '</i></div><div class="list-links">' + links + '</div></li>';
    }).join('') + '</ol>';
  }
}());
