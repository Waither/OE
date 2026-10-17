import homeView from '../../views/home.html?raw';
import p1View from '../../views/P1.html?raw';
import p2View from '../../views/P2.html?raw';
import p3View from '../../views/P3.html?raw';
import p4View from '../../views/P4.html?raw';

const routes = {
    '/': {
        title: 'Strona główna',
        content: homeView,
    },
    '/1': {
        title: 'Projekt 1',
        content: p1View,
        load: () => import('./projects/p1.js'),
    },
    '/2': {
        title: 'Projekt 2',
        content: p2View,
        load: () => import('./projects/p2.js'),
    },
    '/3': {
        title: 'Projekt 3',
        content: p3View,
        load: () => import('./projects/p3.js'),
    },
    '/4': {
        title: 'Projekt 4',
        content: p4View,
        load: () => import('./projects/p4.js'),
    },
};

let renderSequence = 0;

async function renderRoute(pathname) {
    const route = routes[pathname];
    const main = document.querySelector('#app-main');
    const sequence = ++renderSequence;

    if (!main) {
        throw new Error('Nie znaleziono głównego elementu aplikacji (#app-main).');
    }

    if (!route) {
        document.title = 'OE | Nie znaleziono strony';
        main.innerHTML = '<h1>Nie znaleziono strony</h1><p>Wskazany adres nie istnieje.</p>';
        updateNavigation(pathname);
        return;
    }

    document.title = `OE | ${route.title}`;
    main.innerHTML = route.content;
    updateNavigation(pathname);

    if (route.load) {
        const pageModule = await route.load();
        if (sequence === renderSequence && typeof pageModule.mount === 'function') {
            await pageModule.mount(main);
        }
    }
}

function updateNavigation(pathname) {
    document.querySelectorAll('a[data-router-link]').forEach((link) => {
        const isCurrent = new URL(link.href).pathname === pathname;
        link.classList.toggle('active', isCurrent);
        if (isCurrent) {
            link.setAttribute('aria-current', 'page');
        } else {
            link.removeAttribute('aria-current');
        }
    });
}

document.addEventListener('click', (event) => {
    if (
        event.defaultPrevented
        || event.button !== 0
        || event.metaKey
        || event.ctrlKey
        || event.shiftKey
        || event.altKey
    ) {
        return;
    }

    const target = event.target;
    if (!(target instanceof Element)) {
        return;
    }
    const link = target.closest('a[data-router-link]');
    if (!(link instanceof HTMLAnchorElement) || link.origin !== window.location.origin) {
        return;
    }

    event.preventDefault();
    if (link.pathname !== window.location.pathname) {
        window.history.pushState({}, '', link.pathname);
    }
    void renderRoute(link.pathname);
});

window.addEventListener('popstate', () => {
    void renderRoute(window.location.pathname);
});

void renderRoute(window.location.pathname);
