// 移动端导航切换
const mobileToggle = document.getElementById('mobileToggle');
const navLinks = document.getElementById('navLinks');

if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
    });

    // 点击导航链接时关闭菜单
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
        });
    });
}

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
    const footerLang = footerElement.dataset.footer || 'zh';
    const footerPath = `assets/partials/footer-${footerLang}.html`;
    fetch(footerPath)
        .then(response => response.text())
        .then(html => {
            footerElement.innerHTML = html;
        })
        .catch(() => {
            // 保持静默，避免影响页面其他功能
        });
}

// 子页面导航栏注入（统一维护）
const subnavElement = document.getElementById('siteSubnav');
if (subnavElement) {
    const subnavLang = subnavElement.dataset.subnav || 'zh';
    const subnavTitle = subnavElement.dataset.subnavTitle || '';
    const subnavPath = `assets/partials/subnav-${subnavLang}.html`;
    fetch(subnavPath)
        .then(response => response.text())
        .then(html => {
            subnavElement.innerHTML = html.replace('{{TITLE}}', subnavTitle);
        })
        .catch(() => {
            // 保持静默，避免影响页面其他功能
        });
}
