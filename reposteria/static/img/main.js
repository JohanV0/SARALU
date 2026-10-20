/* ============================================================
   SARALU — main.js
   v1.0
   ============================================================ */

/* ============================================================
   PANEL ADMIN — Drawer lateral
   ============================================================ */

function toggleAdminPanel() {
  const drawer  = document.getElementById('admin-drawer');
  const overlay = document.getElementById('admin-overlay');

  if (!drawer || !overlay) return;

  const isOpen = !drawer.classList.contains('-translate-x-full');

  if (isOpen) {
    drawer.classList.add('-translate-x-full');
    overlay.classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
  } else {
    drawer.classList.remove('-translate-x-full');
    overlay.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
  }
}


/* ============================================================
   MENÚ DE USUARIO — Dropdown navbar
   ============================================================ */

function toggleUserMenu(event) {
  if (event) event.stopPropagation();

  const dropdown = document.getElementById('user-menu-dropdown');
  const chevron  = document.getElementById('user-menu-chevron');
  const button   = document.getElementById('user-menu-button');

  if (!dropdown) return;

  const isOpen = !dropdown.classList.contains('hidden');

  if (isOpen) {
    closeUserMenu();
  } else {
    dropdown.classList.remove('hidden');
    if (chevron) chevron.classList.add('rotate-180');
    if (button)  button.setAttribute('aria-expanded', 'true');
  }
}

function closeUserMenu() {
  const dropdown = document.getElementById('user-menu-dropdown');
  const chevron  = document.getElementById('user-menu-chevron');
  const button   = document.getElementById('user-menu-button');

  if (!dropdown) return;

  dropdown.classList.add('hidden');
  if (chevron) chevron.classList.remove('rotate-180');
  if (button)  button.setAttribute('aria-expanded', 'false');
}

function openAdminFromMenu(event) {
  if (event) event.stopPropagation();

  closeUserMenu();

  const drawer  = document.getElementById('admin-drawer');
  const overlay = document.getElementById('admin-overlay');

  if (drawer && overlay) {
    drawer.classList.remove('-translate-x-full');
    overlay.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
  }
}


/* ============================================================
   LISTENERS GLOBALES
   ============================================================ */

document.addEventListener('click', function (e) {
  const wrapper = document.getElementById('user-menu-wrapper');
  const dropdown = document.getElementById('user-menu-dropdown');

  if (!wrapper || !dropdown) return;

  if (!wrapper.contains(e.target)) {
    closeUserMenu();
  }
});

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    closeUserMenu();
  }
});