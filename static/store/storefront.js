(() => {
  const carousel = document.querySelector("[data-carousel]");
  if (carousel) {
    const slides = Array.from(carousel.querySelectorAll("[data-slide]"));
    const dots = Array.from(carousel.querySelectorAll("[data-carousel-dot]"));
    let current = Math.max(0, slides.findIndex((slide) => slide.classList.contains("is-active")));
    let timer = null;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const show = (index) => {
      current = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => {
        const active = i === current;
        slide.classList.toggle("is-active", active);
        slide.setAttribute("aria-hidden", String(!active));
        slide.inert = !active;
      });
      dots.forEach((dot, i) => {
        if (i === current) dot.setAttribute("aria-current", "true");
        else dot.removeAttribute("aria-current");
      });
    };
    const stop = () => { if (timer) window.clearInterval(timer); timer = null; };
    const start = () => {
      stop();
      if (!reducedMotion && slides.length > 1) timer = window.setInterval(() => show(current + 1), 5200);
    };
    carousel.querySelector("[data-carousel-prev]")?.addEventListener("click", () => { show(current - 1); start(); });
    carousel.querySelector("[data-carousel-next]")?.addEventListener("click", () => { show(current + 1); start(); });
    dots.forEach((dot) => dot.addEventListener("click", () => { show(Number(dot.dataset.carouselDot)); start(); }));
    carousel.addEventListener("mouseenter", stop);
    carousel.addEventListener("mouseleave", start);
    carousel.addEventListener("focusin", stop);
    carousel.addEventListener("focusout", (event) => { if (!carousel.contains(event.relatedTarget)) start(); });
    document.addEventListener("visibilitychange", () => document.hidden ? stop() : start());
    show(current);
    start();
  }

  const variantSelect = document.querySelector("[data-variant-select]");
  const priceDisplay = document.querySelector("[data-price-display]");
  if (variantSelect && priceDisplay) {
    const sale = priceDisplay.querySelector("[data-sale-price]");
    const mrp = priceDisplay.querySelector("[data-mrp-label]");
    const discount = priceDisplay.querySelector("[data-discount]");
    const format = (amount) => new Intl.NumberFormat("en-IN").format(amount);
    variantSelect.addEventListener("change", () => {
      const option = variantSelect.selectedOptions[0];
      if (!option || !option.dataset.price) return;
      const currentPrice = Number(option.dataset.price);
      const compareAt = Number(option.dataset.mrp || variantSelect.dataset.mrp || 0);
      sale.textContent = "₹" + format(currentPrice);
      if (mrp) {
        mrp.hidden = !compareAt;
        mrp.textContent = compareAt ? "MRP ₹" + format(compareAt) : "";
      }
      if (discount) {
        const pct = compareAt > currentPrice ? Math.floor((compareAt - currentPrice) * 100 / compareAt) : 0;
        discount.hidden = !pct;
        discount.textContent = pct ? pct + "% OFF" : "";
      }
    });
  }
})();
