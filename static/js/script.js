
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".alert").forEach((alert) => {
        setTimeout(() => {
            if (window.bootstrap) bootstrap.Alert.getOrCreateInstance(alert).close();
        }, 5000);
    });

    document.querySelectorAll("[data-toggle-password]").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.togglePassword);
            if (!input) return;
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            button.querySelector("i").className = show ? "bi bi-eye-slash" : "bi bi-eye";
        });
    });

    const themeButton = document.getElementById("theme-toggle");
    const themeIcon = document.getElementById("theme-icon");
    const themeLabel = document.getElementById("theme-label");

    if (themeButton) {
        const updateButton = (theme) => {
            if (theme === "dark") {
                themeIcon.className = "bi bi-sun-fill";
                themeLabel.textContent = "Light mode";
                themeButton.title = "Switch to light mode";
            } else {
                themeIcon.className = "bi bi-moon-stars-fill";
                themeLabel.textContent = "Dark mode";
                themeButton.title = "Switch to dark mode";
            }
        };

        updateButton(document.documentElement.getAttribute("data-bs-theme"));

        themeButton.addEventListener("click", () => {
            const current = document.documentElement.getAttribute("data-bs-theme");
            const next = current === "dark" ? "light" : "dark";

            document.documentElement.setAttribute("data-bs-theme", next);
            updateButton(next);

            try {
                localStorage.setItem("theme", next);
            } catch (error) {
                
            }
        });
    }

    const strip = document.getElementById("gallery-strip");
    const mainImage = document.getElementById("gallery-main");

    if (strip && mainImage) {
        let isDragging = false;
        let startX = 0;
        let startScroll = 0;
        let moved = false;

        strip.addEventListener("mousedown", (event) => {
            isDragging = true;
            moved = false;
            startX = event.pageX;
            startScroll = strip.scrollLeft;
            strip.classList.add("dragging");
        });

        window.addEventListener("mousemove", (event) => {
            if (!isDragging) return;
            const distance = event.pageX - startX;
            if (Math.abs(distance) > 5) moved = true;
            strip.scrollLeft = startScroll - distance;
        });

        window.addEventListener("mouseup", () => {
            isDragging = false;
            strip.classList.remove("dragging");
        });

        strip.querySelectorAll(".gallery-thumb").forEach((thumb) => {
            thumb.addEventListener("click", () => {
                if (moved) return;

                mainImage.src = thumb.dataset.full;
                mainImage.alt = thumb.alt;

                strip.querySelectorAll(".gallery-thumb").forEach((other) => {
                    other.classList.remove("active");
                });
                thumb.classList.add("active");
            });
        });
    }
});
