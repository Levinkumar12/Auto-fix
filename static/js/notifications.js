/**
 * ========================================================
 * Auto Fix VSMS — Workshop Live Pop-Up Notifications
 * Real-time notification poller and synthesized audio chime
 * ========================================================
 */

// Web Audio synthesized bell sound (no external audio files needed)
function playNotificationChime() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, ctx.currentTime);       // D5 note
        osc.frequency.setValueAtTime(880, ctx.currentTime + 0.15);     // A5 note
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.8);
    } catch (e) {
        // AudioContext might be blocked until user interacts with the page
    }
}

let activeNotificationId = null;
const seenNotificationIds = new Set();

function checkWorkshopNotifications() {
    fetch('/mechanic/api/notifications/unread/')
        .then(response => {
            if (!response.ok) return null;
            return response.json();
        })
        .then(data => {
            if (data && data.notifications && data.notifications.length > 0) {
                const notif = data.notifications[0];
                if (!seenNotificationIds.has(notif.id)) {
                    seenNotificationIds.add(notif.id);
                    activeNotificationId = notif.id;

                    const titleEl = document.getElementById('notifModalTitle');
                    const headlineEl = document.getElementById('notifModalHeadline');
                    const bodyEl = document.getElementById('notifModalBody');
                    const timeEl = document.getElementById('notifModalTime');
                    const actionBtn = document.getElementById('notifActionBtn');

                    if (titleEl) titleEl.innerText = notif.title;
                    if (headlineEl) headlineEl.innerText = notif.title;
                    if (bodyEl) bodyEl.innerText = notif.message;
                    if (timeEl) timeEl.innerText = 'Received at ' + notif.created_at;
                    if (actionBtn) actionBtn.setAttribute('href', notif.action_url || '/mechanic/jobs/active/');

                    playNotificationChime();

                    const modalEl = document.getElementById('workshopNotificationModal');
                    if (modalEl && window.bootstrap) {
                        const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
                        modal.show();
                    }
                }
            }
        })
        .catch(err => {
            // Network quiet fallback
        });
}

function dismissCurrentNotification() {
    if (activeNotificationId) {
        const tokenHolder = document.getElementById('csrf_token_holder');
        const token = tokenHolder ? tokenHolder.getAttribute('data-token') : '';
        fetch('/mechanic/api/notifications/' + activeNotificationId + '/read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json'
            }
        }).catch(e => {});
        activeNotificationId = null;
    }
}

// Initialize polling when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Poll every 4 seconds
    setInterval(checkWorkshopNotifications, 4000);
    // Initial check after 1.5 seconds
    setTimeout(checkWorkshopNotifications, 1500);
});

