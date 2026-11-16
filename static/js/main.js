/**
 * ========================================================
 * Auto Fix VSMS — Main Client-Side Interactions
 * ========================================================
 */

document.addEventListener('DOMContentLoaded', function () {
    // --------------------------------------------------------
    // 1. Live Estimate Calculator (Mechanic Portal)
    // --------------------------------------------------------
    const labourInput = document.getElementById('id_estimated_labour');
    const partsInput = document.getElementById('id_estimated_parts');
    const totalDisplay = document.getElementById('total_estimate_display');

    if (labourInput && partsInput && totalDisplay) {
        function calculateEstimateTotal() {
            const labour = parseFloat(labourInput.value) || 0;
            const parts = parseFloat(partsInput.value) || 0;
            const total = labour + parts;
            totalDisplay.innerText = '₹' + total.toFixed(2);
        }

        labourInput.addEventListener('input', calculateEstimateTotal);
        partsInput.addEventListener('input', calculateEstimateTotal);
        calculateEstimateTotal();
    }

    // --------------------------------------------------------
    // 2. Dynamic Service Type Tip (Customer Booking Page)
    // --------------------------------------------------------
    const serviceSelect = document.getElementById('service_select');
    const estimateTip = document.getElementById('estimate_tip');

    if (serviceSelect && estimateTip) {
        function checkServiceType() {
            const selected = serviceSelect.options[serviceSelect.selectedIndex];
            if (selected && selected.getAttribute('data-type') === 'ESTIMATE') {
                estimateTip.classList.remove('d-none');
            } else {
                estimateTip.classList.add('d-none');
            }
        }

        serviceSelect.addEventListener('change', checkServiceType);
        checkServiceType();
    }

    // --------------------------------------------------------
    // 3. Payment Method Switcher (UPI QR vs Cash)
    // --------------------------------------------------------
    const upiRadio = document.getElementById('id_payment_method_0');
    const cashRadio = document.getElementById('id_payment_method_1');
    const upiPanel = document.getElementById('upi_payment_panel');
    const cashPanel = document.getElementById('cash_payment_panel');
    const cardUpi = document.getElementById('method_card_upi');
    const cardCash = document.getElementById('method_card_cash');

    if (upiRadio && cashRadio && upiPanel && cashPanel) {
        function updatePaymentMethod() {
            if (upiRadio.checked) {
                upiPanel.classList.remove('d-none');
                cashPanel.classList.add('d-none');
                if (cardUpi) cardUpi.classList.add('active');
                if (cardCash) cardCash.classList.remove('active');
            } else if (cashRadio.checked) {
                upiPanel.classList.add('d-none');
                cashPanel.classList.remove('d-none');
                if (cardUpi) cardUpi.classList.remove('active');
                if (cardCash) cardCash.classList.add('active');
            }
        }

        upiRadio.addEventListener('change', updatePaymentMethod);
        cashRadio.addEventListener('change', updatePaymentMethod);

        if (cardUpi) {
            cardUpi.addEventListener('click', function () {
                upiRadio.checked = true;
                updatePaymentMethod();
            });
        }
        if (cardCash) {
            cardCash.addEventListener('click', function () {
                cashRadio.checked = true;
                updatePaymentMethod();
            });
        }
    }
});

// One-shot, reduced-motion-aware counter reveal for homepage statistics.
document.addEventListener('DOMContentLoaded', function () {
    const counters = document.querySelectorAll('.home-counter[data-target]');
    if (!counters.length) return;

    const numberFormat = new Intl.NumberFormat();
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function revealCounter(counter) {
        const target = Number.parseInt(counter.dataset.target, 10);
        if (!Number.isFinite(target)) return;
        if (reducedMotion || target <= 0) {
            counter.textContent = numberFormat.format(target);
            return;
        }

        const startedAt = performance.now();
        const duration = 850;
        function frame(now) {
            const progress = Math.min((now - startedAt) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            counter.textContent = numberFormat.format(Math.round(target * eased));
            if (progress < 1) requestAnimationFrame(frame);
        }
        requestAnimationFrame(frame);
    }

    if (!('IntersectionObserver' in window)) {
        counters.forEach(revealCounter);
        return;
    }

    const observer = new IntersectionObserver((entries, activeObserver) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            revealCounter(entry.target);
            activeObserver.unobserve(entry.target);
        });
    }, { threshold: 0.35 });

    counters.forEach(counter => observer.observe(counter));
});

