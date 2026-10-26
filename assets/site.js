(() => {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const desktopScene = matchMedia('(min-width: 1280px)');
  const ease = 'cubic-bezier(.16,1,.3,1)';
  const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
  const toggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('#nav-menu');
  const nav = document.querySelector('.floating-nav');
  let menuAnimation;
  let menuGeneration = 0;

  function setMenu(open) {
    const generation = ++menuGeneration;
    const previousHeight = menu.hidden ? 0 : menu.getBoundingClientRect().height;
    menuAnimation?.cancel();
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    menu.inert = !open;
    if (reducedMotion.matches) {
      menu.hidden = !open;
      menu.style.height = '';
      return;
    }
    menu.hidden = false;
    menu.style.height = 'auto';
    const naturalHeight = menu.getBoundingClientRect().height;
    menuAnimation = menu.animate([
      { height: `${previousHeight}px`, opacity: open ? 0.6 : 1 },
      { height: `${open ? naturalHeight : 0}px`, opacity: open ? 1 : 0 },
    ], { duration: open ? 800 : 450, easing: ease, fill: 'both' });
    if (open) {
      menu.querySelectorAll('a').forEach((link, index) => {
        link.animate([
          { opacity: 0, transform: 'translateX(-20px)' },
          { opacity: 1, transform: 'translateX(0)' },
        ], { duration: 800, delay: 100 + index * 100, easing: ease, fill: 'backwards' });
      });
    }
    menuAnimation.finished.then(() => {
      if (generation !== menuGeneration) return;
      menu.hidden = !open;
      menu.style.height = '';
      menuAnimation.cancel();
    }).catch(() => {});
  }

  toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  menu.addEventListener('click', event => {
    if (event.target.closest('a')) setMenu(false);
  });
  document.addEventListener('click', event => {
    if (!menu.hidden && !nav.contains(event.target)) setMenu(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      toggle.focus();
    }
  });

  // RollingTextHover: a second line is provided by text-shadow, with staggered letters.
  document.querySelectorAll('.nav-menu a, .footer-links a, .button').forEach(link => {
    const textNode = [...link.childNodes].find(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
    if (!textNode) return;
    const label = textNode.textContent;
    const wrapper = document.createElement('span');
    wrapper.className = 'roll-label';
    wrapper.setAttribute('aria-hidden', 'true');
    Array.from(label).forEach((letter, index) => {
      const char = document.createElement('span');
      char.className = 'roll-char';
      char.style.setProperty('--letter', index);
      char.textContent = letter === ' ' ? '\u00a0' : letter;
      wrapper.append(char);
    });
    if (!link.hasAttribute('aria-label')) link.setAttribute('aria-label', label.trim());
    textNode.replaceWith(wrapper);
  });
  document.querySelectorAll('.arrow-box').forEach(box => {
    const copy = box.querySelector('svg')?.cloneNode(true);
    if (copy) {
      copy.classList.add('arrow-clone');
      box.append(copy);
    }
  });

  function splitWords(element, className) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    const words = [];
    textNodes.forEach(node => {
      const fragment = document.createDocumentFragment();
      node.textContent.split(/(\s+)/).forEach(part => {
        if (!part.trim()) {
          fragment.append(document.createTextNode(part));
          return;
        }
        const word = document.createElement('span');
        word.className = className;
        word.textContent = part;
        words.push(word);
        fragment.append(word);
      });
      node.replaceWith(fragment);
    });
    return words;
  }

  const scene = document.querySelector('.intro-scene');
  const hero = document.querySelector('.hero');
  const portrait = document.querySelector('.portrait-card');
  const statement = document.querySelector('.scroll-statement');
  const scrollWords = statement ? splitWords(statement, 'scroll-word') : [];
  let sceneStart = 0;
  let heroHeight = innerHeight;
  let statementTop = 0;
  let portraitProgress = 0;
  let scrollFrame = 0;
  let lastFrame = 0;

  function measureScene() {
    if (scene) sceneStart = scene.getBoundingClientRect().top + scrollY;
    if (hero) heroHeight = hero.offsetHeight;
    if (statement) statementTop = statement.getBoundingClientRect().top + scrollY;
    requestScrollUpdate();
  }

  function updateScroll(time) {
    scrollFrame = 0;
    const dt = Math.min((time - (lastFrame || time - 16.7)) / 1000, 0.05);
    lastFrame = time;
    let unsettled = false;
    if (portrait && desktopScene.matches) {
      const target = reducedMotion.matches ? 0 : clamp((scrollY - sceneStart) / heroHeight);
      portraitProgress += (target - portraitProgress) * (1 - Math.exp(-22 * dt));
      if (Math.abs(target - portraitProgress) < 0.0001) portraitProgress = target;
      else unsettled = true;
      // Reference: scale .5 to 1, translateY 114 to 0, rotateY 0 to 180.
      const progress = portraitProgress;
      portrait.style.transform = `translateY(${114 * (1 - progress)}px) scale(${0.5 + progress * 0.5}) rotateY(${180 * progress}deg)`;
    } else if (portrait) {
      portrait.style.transform = '';
    }
    if (statement) {
      const start = statementTop - innerHeight * 0.8;
      const end = statementTop - innerHeight * 0.35;
      const progress = reducedMotion.matches ? 1 : clamp((scrollY - start) / Math.max(end - start, 1));
      scrollWords.forEach((word, index) => {
        const alpha = 0.1 + clamp(progress * scrollWords.length - index + 1) * 0.9;
        word.style.color = `rgba(17,17,17,${alpha.toFixed(3)})`;
      });
    }
    if (unsettled) requestScrollUpdate();
  }

  function requestScrollUpdate() {
    if (!scrollFrame) scrollFrame = requestAnimationFrame(updateScroll);
  }
  addEventListener('scroll', requestScrollUpdate, { passive: true });
  addEventListener('resize', measureScene);
  addEventListener('load', measureScene, { once: true });
  document.fonts.ready.then(measureScene);
  desktopScene.addEventListener('change', measureScene);
  reducedMotion.addEventListener('change', measureScene);
  measureScene();

  // Entrances use the durations, distances and word stagger of the reference.
  if (!reducedMotion.matches && 'IntersectionObserver' in window) {
    const entrances = new Map();
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entrances.get(entry.target)?.forEach(animation => animation.play());
        observer.unobserve(entry.target);
      });
    }, { threshold: 0 });

    function reveal(element, frames, options) {
      const animation = element.animate(frames, { ...options, easing: ease, fill: 'both' });
      animation.pause();
      entrances.set(element, [animation]);
      observer.observe(element);
    }

    document.querySelectorAll('h1, h2, .contact-copy > p').forEach(heading => {
      const isHero = heading.closest('.hero');
      const words = splitWords(heading, 'word-token');
      const animations = words.map((word, index) => {
        const animation = word.animate([
          { opacity: 0.001, filter: `blur(${isHero ? 2 : 10}px)`, transform: 'translateY(10px)' },
          { opacity: 1, filter: 'blur(0px)', transform: 'translateY(0)' },
        ], { duration: isHero ? 2800 : 1800, delay: index * (isHero ? 250 : 50), easing: ease, fill: 'both' });
        animation.pause();
        return animation;
      });
      entrances.set(heading, animations);
      observer.observe(heading);
    });
    document.querySelectorAll('.project-card, .value, .gallery-image, .gallery-video, .detail-cover').forEach((element, index) => {
      reveal(element, [{ opacity: 0, transform: 'translateY(20px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 1600, delay: 100 + index % 2 * 100 });
    });
    document.querySelectorAll('.about-copy, .intro-name, .about-intro > .eyebrow, .footer-links, .footer-wordmark, .contact-links').forEach(element => {
      reveal(element, [{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 1600, delay: 200 });
    });
    document.querySelector('.floating-nav').animate([
      { opacity: 0, transform: 'translateY(40px)' },
      { opacity: 1, transform: 'translateY(0)' },
    ], { duration: 2200, easing: ease });
    document.querySelectorAll('.hero-shape, .hero-bottom, .portrait-enter').forEach(element => {
      element.animate([
        { opacity: 0, transform: 'translateY(10px)' },
        { opacity: 1, transform: 'translateY(0)' },
      ], { duration: 1600, delay: 1400, easing: ease, fill: 'backwards' });
    });
    if (portrait && !desktopScene.matches) {
      portrait.animate([{ transform: 'rotateY(0deg)' }, { transform: 'rotateY(180deg)' }], { duration: 1600, delay: 2000, easing: ease, fill: 'backwards' });
    }
    reducedMotion.addEventListener('change', () => {
      if (reducedMotion.matches) document.getAnimations().forEach(animation => animation.finish());
    });
  }

  // The two decorative objects can be dragged and retain a short inertial movement.
  document.querySelectorAll('.hero-shape').forEach(shape => {
    let drag;
    let position = { x: 0, y: 0 };
    let inertia;
    const paint = () => { shape.style.translate = `${position.x}px ${position.y}px`; };
    shape.addEventListener('pointerdown', event => {
      if (reducedMotion.matches || event.button !== 0) return;
      cancelAnimationFrame(inertia);
      drag = { id: event.pointerId, x: event.clientX, y: event.clientY, time: performance.now(), vx: 0, vy: 0 };
      shape.setPointerCapture(event.pointerId);
      shape.classList.add('is-dragging');
      event.preventDefault();
    });
    shape.addEventListener('pointermove', event => {
      if (!drag || drag.id !== event.pointerId) return;
      const now = performance.now();
      const dt = Math.max(now - drag.time, 8);
      const dx = event.clientX - drag.x;
      const dy = event.clientY - drag.y;
      position.x += dx;
      position.y += dy;
      drag = { ...drag, x: event.clientX, y: event.clientY, time: now, vx: dx / dt * 16, vy: dy / dt * 16 };
      paint();
    });
    function endDrag(event) {
      if (!drag || drag.id !== event.pointerId) return;
      let { vx, vy, time } = drag;
      if (performance.now() - time > 100) vx = vy = 0;
      drag = null;
      shape.classList.remove('is-dragging');
      function coast() {
        vx *= 0.9;
        vy *= 0.9;
        position.x += vx;
        position.y += vy;
        paint();
        if (Math.abs(vx) + Math.abs(vy) > 0.1) inertia = requestAnimationFrame(coast);
      }
      if (event.type !== 'pointercancel') inertia = requestAnimationFrame(coast);
    }
    shape.addEventListener('pointerup', endDrag);
    shape.addEventListener('pointercancel', endDrag);
  });

  // Desktop wheel interpolation mirrors the reference's smooth scrolling.
  let wheelFrame = 0;
  let wheelTarget = scrollY;
  let wheelCurrent = scrollY;
  let wheelTime = 0;
  function stopWheel() {
    cancelAnimationFrame(wheelFrame);
    wheelFrame = 0;
    wheelCurrent = wheelTarget = scrollY;
  }
  function smoothWheel(time) {
    const dt = Math.min((time - (wheelTime || time - 16.7)) / 16.7, 3);
    wheelTime = time;
    wheelCurrent += (wheelTarget - wheelCurrent) * (1 - Math.pow(0.88, dt));
    if (Math.abs(wheelTarget - wheelCurrent) < 0.5) wheelCurrent = wheelTarget;
    window.scrollTo({ top: wheelCurrent, behavior: 'instant' });
    if (wheelCurrent !== wheelTarget) wheelFrame = requestAnimationFrame(smoothWheel);
    else wheelFrame = 0;
  }
  addEventListener('wheel', event => {
    if (reducedMotion.matches || !matchMedia('(pointer:fine)').matches || event.ctrlKey || event.metaKey || event.shiftKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
    for (const element of event.composedPath()) {
      if (!(element instanceof Element) || element === document.documentElement || element === document.body) continue;
      if (element.matches('input,textarea,select,video')) return;
      if (element.scrollHeight > element.clientHeight + 1 && /auto|scroll/.test(getComputedStyle(element).overflowY)) return;
    }
    event.preventDefault();
    if (!wheelFrame) wheelCurrent = wheelTarget = scrollY;
    const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? innerHeight : 1);
    wheelTarget = clamp(wheelTarget + delta, 0, document.documentElement.scrollHeight - innerHeight);
    if (!wheelFrame) {
      wheelTime = 0;
      wheelFrame = requestAnimationFrame(smoothWheel);
    }
  }, { passive: false });
  addEventListener('keydown', event => {
    if (['ArrowDown', 'ArrowUp', 'PageDown', 'PageUp', 'Home', 'End', ' '].includes(event.key)) stopWheel();
  });
  addEventListener('pointerdown', stopWheel, { passive: true });
  addEventListener('touchstart', stopWheel, { passive: true });
  document.addEventListener('click', event => {
    if (event.target.closest('a')) stopWheel();
  });
  reducedMotion.addEventListener('change', stopWheel);
})();
