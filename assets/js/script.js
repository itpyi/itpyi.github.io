// 移动端导航切换（使用事件委托，兼容异步注入的子页面导航栏）
document.addEventListener('click', e => {
    if (e.target.closest('#mobileToggle')) {
        document.getElementById('navLinks')?.classList.toggle('active');
    } else if (e.target.closest('.nav-links a')) {
        document.getElementById('navLinks')?.classList.remove('active');
    }
});

// 滚动时高亮当前导航链接
const navAnchors = document.querySelectorAll('.nav-links a[href^="#"]');
if (navAnchors.length > 0) {
    const sectionObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                navAnchors.forEach(a => {
                    a.classList.toggle('active', a.getAttribute('href') === `#${id}`);
                });
            }
        });
    }, { rootMargin: '-20% 0px -70% 0px' });

    document.querySelectorAll('section[id]').forEach(section => {
        sectionObserver.observe(section);
    });
}

// 平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        // 如果是普通的锚点跳转，才进行 preventDefault
        // 如果是跨页面跳转（没有找到 targetElement），则保持默认行为
        
        const targetId = this.getAttribute('href');
        if (targetId === '#' || !targetId.startsWith('#')) return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            e.preventDefault();
            const headerOffset = 80;
            const elementPosition = targetElement.getBoundingClientRect().top;
            const offsetPosition = elementPosition - headerOffset;
            
            window.scrollBy({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// 页脚注入（统一维护）
const footerElement = document.getElementById('siteFooter');
if (footerElement) {
    const footerPath = 'assets/partials/footer.html';

    const syncHomepageFooterHeight = () => {
        const homepageShell = document.querySelector('.homepage-shell');
        if (!homepageShell || !footerElement) return;
        const footerHeight = footerElement.offsetHeight;
        document.documentElement.style.setProperty('--footer-height', `${footerHeight}px`);
    };

    fetch(footerPath)
        .then(response => response.text())
        .then(html => {
            footerElement.innerHTML = html;
            syncHomepageFooterHeight();
        })
        .catch(() => {
            // 保持静默，避免影响页面其他功能
        });

    window.addEventListener('resize', syncHomepageFooterHeight);
}

// 子页面导航栏注入（统一维护）
const subnavElement = document.getElementById('siteSubnav');
if (subnavElement) {
    const subnavTitleZh = subnavElement.dataset.subnavTitleZh || subnavElement.dataset.subnavTitle || '';
    const subnavTitleEn = subnavElement.dataset.subnavTitleEn || subnavElement.dataset.subnavTitle || '';
    const subnavPath = 'assets/partials/subnav.html';
    fetch(subnavPath)
        .then(response => response.text())
        .then(html => {
            // Replace both language placeholders
            html = html.replace('{{TITLE_ZH}}', subnavTitleZh);
            html = html.replace('{{TITLE_EN}}', subnavTitleEn);
            subnavElement.innerHTML = html;
        })
        .catch(() => {
            // 保持静默，避免影响页面其他功能
        });
}

// ========================================
// Language Switcher Functionality
// ========================================

// Toggle language menu visibility
document.addEventListener('click', e => {
    const langButton = e.target.closest('.lang-button');
    const langSwitcher = e.target.closest('.lang-switcher');
    
    if (langButton) {
        // Toggle the dropdown menu for this switcher
        const switcher = langButton.closest('.lang-switcher');
        const isActive = switcher.classList.contains('active');
        
        // Close all other open menus
        document.querySelectorAll('.lang-switcher.active').forEach(s => {
            if (s !== switcher) s.classList.remove('active');
        });
        
        // Toggle current menu
        switcher.classList.toggle('active', !isActive);
    } else if (!langSwitcher) {
        // Click outside - close all menus
        document.querySelectorAll('.lang-switcher.active').forEach(s => {
            s.classList.remove('active');
        });
    }
});

// Handle language menu item clicks
document.addEventListener('click', e => {
    const menuItem = e.target.closest('.lang-menu li');
    if (!menuItem) return;
    
    const targetLang = menuItem.dataset.lang;
    if (!targetLang) return;
    
    // Find the parent section
    const section = menuItem.closest('.lang-switchable');
    if (!section) return;
    
    // Update menu active state
    const menu = menuItem.closest('.lang-menu');
    menu.querySelectorAll('li').forEach(li => {
        li.classList.toggle('active', li === menuItem);
    });
    
    // Switch content visibility
    section.querySelectorAll('.lang-content').forEach(content => {
        if (content.dataset.lang === targetLang) {
            content.classList.add('active');
            content.style.display = 'block';
        } else {
            content.classList.remove('active');
            content.style.display = 'none';
        }
    });
    
    // Switch h2 title visibility
    section.querySelectorAll('.section-header h2').forEach(h2 => {
        if (h2.dataset.lang === targetLang) {
            h2.style.display = 'block';
        } else {
            h2.style.display = 'none';
        }
    });
    
    // Close the menu
    menuItem.closest('.lang-switcher').classList.remove('active');
});

// ========================================
// Global Language Switcher Functionality
// ========================================

// Function to switch global language
function switchGlobalLanguage(targetLang) {
    // 1. Update HTML lang attribute
    document.documentElement.lang = targetLang === 'zh' ? 'zh-Hans' : 'en';
    
    // 2. Update meta description
    const metaDescriptions = document.querySelectorAll('meta[name="description"]');
    metaDescriptions.forEach(meta => {
        if (meta.dataset.lang === targetLang) {
            // Move this meta to be the active one by updating the first meta tag
            const firstMeta = document.querySelector('meta[name="description"]');
            if (firstMeta && meta.hasAttribute('content')) {
                firstMeta.setAttribute('content', meta.getAttribute('content'));
            }
        }
    });
    
    // 3. Update page title
    const titleElements = document.querySelectorAll('head title[data-lang]');
    titleElements.forEach(title => {
        if (title.dataset.lang === targetLang) {
            document.title = title.textContent;
        }
    });
    
    // 4. Switch all data-lang elements (except meta, title, and menu items)
    document.querySelectorAll('[data-lang]').forEach(elem => {
        // Skip meta and title tags as they're handled specially
        if (elem.tagName === 'META' || elem.tagName === 'TITLE') return;
        
        // Skip language menu items (both section and global menus)
        if (elem.tagName === 'LI' && (elem.closest('.lang-menu') || elem.closest('.global-lang-menu'))) return;
        
        if (elem.dataset.lang === targetLang) {
            elem.style.display = '';
        } else {
            elem.style.display = 'none';
        }
    });
    
    // 5. Update all lang-switchable sections
    document.querySelectorAll('.lang-switchable').forEach(section => {
        // Check if this section has the target language
        const hasTargetLang = section.querySelector(`.lang-content[data-lang="${targetLang}"]`);
        const langToShow = hasTargetLang ? targetLang : 'zh'; // Fallback to Chinese if target lang not available
        
        // Switch content
        section.querySelectorAll('.lang-content').forEach(content => {
            if (content.dataset.lang === langToShow) {
                content.classList.add('active');
                content.style.display = 'block';
            } else {
                content.classList.remove('active');
                content.style.display = 'none';
            }
        });
        
        // Switch section header titles
        section.querySelectorAll('.section-header h2').forEach(h2 => {
            if (h2.dataset.lang === langToShow) {
                h2.style.display = 'block';
            } else {
                h2.style.display = 'none';
            }
        });
        
        // Update section's language menu active state
        section.querySelectorAll('.lang-menu li').forEach(li => {
            li.classList.toggle('active', li.dataset.lang === langToShow);
        });
    });
    
    // 6. Update global language menu active state
    document.querySelectorAll('.global-lang-menu li').forEach(li => {
        li.classList.toggle('active', li.dataset.lang === targetLang);
    });
}

// Toggle global language menu visibility
document.addEventListener('click', e => {
    const globalLangButton = e.target.closest('.global-lang-button');
    const globalLangSwitcher = e.target.closest('.global-lang-switcher');
    
    if (globalLangButton) {
        // Toggle the dropdown menu for global switcher
        const switcher = globalLangButton.closest('.global-lang-switcher');
        const isActive = switcher.classList.contains('active');
        
        // Close all other open menus (both global and section)
        document.querySelectorAll('.global-lang-switcher.active, .lang-switcher.active').forEach(s => {
            if (s !== switcher) s.classList.remove('active');
        });
        
        // Toggle current menu
        switcher.classList.toggle('active', !isActive);
    } else if (!globalLangSwitcher) {
        // Click outside - close global language menu
        document.querySelectorAll('.global-lang-switcher.active').forEach(s => {
            s.classList.remove('active');
        });
    }
});

// Handle global language menu item clicks
document.addEventListener('click', e => {
    const menuItem = e.target.closest('.global-lang-menu li');
    if (!menuItem) return;
    
    const targetLang = menuItem.dataset.lang;
    if (!targetLang) return;
    
    // Switch to the selected language
    switchGlobalLanguage(targetLang);
    
    // Close the menu
    menuItem.closest('.global-lang-switcher').classList.remove('active');
});

// ========================================
// Homepage entrance transition
// ========================================

const homepageShell = document.querySelector('.homepage-shell');
const coverEnterZone = document.querySelector('.cover-enter-zone');

if (homepageShell && coverEnterZone) {
    const enterHomepage = () => {
        if (homepageShell.classList.contains('home-entered')) return;
        homepageShell.classList.add('home-entered');
        coverEnterZone.setAttribute('aria-hidden', 'true');
        coverEnterZone.blur();
    };

    coverEnterZone.addEventListener('click', enterHomepage);
    coverEnterZone.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            enterHomepage();
        }
    });
}
