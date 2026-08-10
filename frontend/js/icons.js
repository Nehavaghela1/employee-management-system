// Shared SVG icon sprite. Injected once per page; icons are referenced via
// <svg class="icon"><use href="#i-name"></use></svg>
(function() {
    var sprite =
        '<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">' +
        '<defs>' +
        '<symbol id="i-building" viewBox="0 0 24 24"><rect x="4" y="3" width="16" height="18"></rect><path d="M9 21v-4h6v4"></path><path d="M8 7h.01M8 11h.01M8 15h.01M16 7h.01M16 11h.01M16 15h.01"></path></symbol>' +
        '<symbol id="i-users" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"></path><circle cx="10" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></symbol>' +
        '<symbol id="i-user" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></symbol>' +
        '<symbol id="i-settings" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"></path></symbol>' +
        '<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path></symbol>' +
        '<symbol id="i-check" viewBox="0 0 24 24"><polyline points="4 12 9 17 20 6"></polyline></symbol>' +
        '<symbol id="i-check-circle" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><polyline points="8 12 11 15 16 9"></polyline></symbol>' +
        '<symbol id="i-x" viewBox="0 0 24 24"><line x1="5" y1="5" x2="19" y2="19"></line><line x1="19" y1="5" x2="5" y2="19"></line></symbol>' +
        '<symbol id="i-alert-triangle" viewBox="0 0 24 24"><path d="M12 3 2 20h20L12 3z"></path><line x1="12" y1="10" x2="12" y2="14"></line><line x1="12" y1="17" x2="12" y2="17.01"></line></symbol>' +
        '<symbol id="i-calendar" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"></rect><line x1="3" y1="10" x2="21" y2="10"></line><line x1="8" y1="3" x2="8" y2="7"></line><line x1="16" y1="3" x2="16" y2="7"></line></symbol>' +
        '<symbol id="i-folder" viewBox="0 0 24 24"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"></path></symbol>' +
        '<symbol id="i-clipboard" viewBox="0 0 24 24"><rect x="6" y="4" width="12" height="17" rx="1.5"></rect><rect x="9" y="2.5" width="6" height="3" rx="1"></rect><line x1="9" y1="11" x2="15" y2="11"></line><line x1="9" y1="15" x2="15" y2="15"></line></symbol>' +
        '<symbol id="i-search" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"></circle><line x1="16" y1="16" x2="21" y2="21"></line></symbol>' +
        '<symbol id="i-chevron-left" viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"></polyline></symbol>' +
        '<symbol id="i-chevron-right" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"></polyline></symbol>' +
        '<symbol id="i-eye" viewBox="0 0 24 24"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"></path><circle cx="12" cy="12" r="3"></circle></symbol>' +
        '<symbol id="i-eye-off" viewBox="0 0 24 24"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a18.6 18.6 0 0 1 4.22-5.06M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 7 11 7a18.6 18.6 0 0 1-2.16 3.19M14.12 14.12a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></symbol>' +
        '<symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z"></path></symbol>' +
        '<symbol id="i-edit" viewBox="0 0 24 24"><path d="M12 20h9"></path><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"></path></symbol>' +
        '</defs></svg>';
    document.currentScript.insertAdjacentHTML('afterend', sprite);
})();
