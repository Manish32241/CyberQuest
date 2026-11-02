const timer = document.querySelector(".timer[data-deadline]");

if (timer) {
    const deadline = Number(timer.dataset.deadline) * 1000;
    const total = Number(timer.dataset.total);
    const value = document.getElementById("timer-value");
    const fill = document.getElementById("timer-fill");
    const timeoutForm = document.getElementById("timeout-form");
    let submitted = false;

    const updateTimer = () => {
        const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
        value.textContent = remaining;
        fill.style.width = `${Math.min(100, (remaining / total) * 100)}%`;
        timer.classList.toggle("timer-low", remaining <= 10);

        if (remaining === 0 && !submitted) {
            submitted = true;
            timeoutForm.requestSubmit();
        }
    };

    updateTimer();
    window.setInterval(updateTimer, 250);
}

document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        if (!window.confirm(form.dataset.confirm)) {
            event.preventDefault();
        }
    });
});
