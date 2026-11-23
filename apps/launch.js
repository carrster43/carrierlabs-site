/* The tap: the icon presses in, its colour opens out to the whole screen, then the app page.
   Used by apps/index.html and the homepage app row. Plain links underneath: reduced motion,
   new-tab clicks and no script all just follow the link. */
(function(){
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  document.documentElement.classList.add('js');
  var overlay = null, timer = null;

  function clear(){
    if (overlay) { overlay.remove(); overlay = null; }
    if (timer) { clearTimeout(timer); timer = null; }
    document.querySelectorAll('.app.pressed').forEach(function(a){ a.classList.remove('pressed'); });
  }
  // Coming back with the Back button restores this page from cache: drop the overlay.
  window.addEventListener('pageshow', clear);

  document.querySelectorAll('.app').forEach(function(a){
    a.addEventListener('pointerdown', function(){ a.classList.add('pressed'); });
    ['pointerup','pointerleave','pointercancel'].forEach(function(t){
      a.addEventListener(t, function(){ a.classList.remove('pressed'); });
    });

    a.addEventListener('click', function(e){
      // New tab, new window, or reduced motion: let the plain link do its job.
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      if (reduce.matches || !('animate' in Element.prototype) || overlay) return;
      e.preventDefault();

      var href = a.href, tile = a.querySelector('.tile'), r = tile.getBoundingClientRect();
      var W = window.innerWidth, H = window.innerHeight;
      var radius = r.width * 0.22;

      overlay = document.createElement('div');
      overlay.className = 'launch';
      overlay.setAttribute('aria-hidden', 'true');
      overlay.style.background = a.dataset.accent || '#151a33';
      var glyph = document.createElement('div');
      var img = tile.querySelector('img');
      if (img) { glyph.className = 'glyph'; glyph.appendChild(img.cloneNode()); }
      else { glyph.className = 'glyph mono'; glyph.textContent = tile.textContent; }
      var title = document.createElement('div');
      title.className = 'title';
      title.textContent = a.querySelector('.name').textContent;
      overlay.appendChild(glyph); overlay.appendChild(title);
      document.body.appendChild(overlay);

      // 1. The colour opens out from the icon's exact spot to the whole screen.
      var from = 'inset(' + r.top + 'px ' + (W - r.right) + 'px ' + (H - r.bottom) + 'px ' + r.left + 'px round ' + radius + 'px)';
      var open = overlay.animate(
        [{ clipPath: from }, { clipPath: 'inset(0px 0px 0px 0px round 0px)' }],
        { duration: 480, easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'forwards' });

      // 2. The icon travels with it from where it sat to the centre, growing as it goes.
      var dx = (r.left + r.width / 2) - W / 2, dy = (r.top + r.height / 2) - H / 2, s = r.width / 96;
      glyph.animate(
        [{ transform: 'translate(' + dx + 'px,' + dy + 'px) scale(' + s + ')' }, { transform: 'none' }],
        { duration: 480, easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'forwards' });

      // 3. The name rises in underneath.
      title.animate(
        [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }],
        { duration: 260, delay: 260, easing: 'ease-out', fill: 'both' });

      var go = function(){ window.location.href = href; };
      open.onfinish = function(){ timer = setTimeout(go, 160); };
      // Safety net: never strand anyone on the colour screen.
      setTimeout(go, 1100);
    });
  });
})();
