(function() {
  'use strict';

  var container = document.getElementById('booklistContent');
  if (!container) return;

  fetch('assets/data/books.json')
    .then(function(response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(function(data) {
      container.innerHTML = renderBookList(data);
    })
    .catch(function() {
      container.innerHTML = '<p style="color: var(--gray-text);">书单加载失败。</p>';
    });

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function renderBookList(data) {
    var html = '';
    data.sections.forEach(function(section) {
      html += '<h2>' + escapeHtml(section.title) + '</h2>';
      html += '<ul class="book-list">';
      section.books.forEach(function(book) {
        html += renderBookItem(book);
      });
      html += '</ul>';
    });
    return html;
  }

  function renderBookItem(book) {
    var parts = [];
    parts.push('<em>' + escapeHtml(book.title) + '</em>');
    parts.push('，' + escapeHtml(book.author));
    parts.push('，' + escapeHtml(book.year) + '，' + escapeHtml(book.publisher));
    if (book.readDate) {
      parts.push('——' + escapeHtml(book.readDate));
    } else {
      parts.push('。');
    }
    return '<li class="book-item">' + parts.join('') + '</li>';
  }
})();
