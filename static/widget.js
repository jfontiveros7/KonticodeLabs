(function () {
  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function initFeedbackWidget() {
    const config = window.KONTICODE_CONFIG || {};
    const feedbackConfig = config.feedback || {};
    const donationOptions = Array.isArray(config.donationOptions) ? config.donationOptions : [];
    const focusableSelector =
      "button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])";

    const supportHeadline = document.getElementById("support-headline");
    const supportNote = document.getElementById("support-note");
    const donateLink = document.getElementById("donate-link");
    const monthlyLink = document.getElementById("monthly-link");
    const donationCards = document.getElementById("donation-cards");
    const checkoutStatus = document.getElementById("checkout-status");
    const feedbackModal = document.getElementById("feedback-modal");
    const feedbackForm = document.getElementById("feedback-form");
    const feedbackStatus = document.getElementById("feedback-status");
    const feedbackSubmit = document.getElementById("feedback-submit");
    const feedbackPage = document.getElementById("feedback-page");
    const openButtons = document.querySelectorAll("[data-open-feedback]");
    const closeButtons = document.querySelectorAll("[data-close-feedback]");

    let lastFocusedElement = null;
    let closeTimerId = null;
    let resetFormOnClose = false;
    let successfulSubmissionsThisOpen = 0;
    let selectedDonationPlan = donationOptions.length ? donationOptions[0].plan : "";

    function renderDonationCards() {
      if (!donationCards) {
        return;
      }

      donationCards.innerHTML = "";

      donationOptions.forEach(function (option) {
        const card = document.createElement("article");
        card.className = "donation-card";
        card.innerHTML =
          "<strong>" +
          escapeHtml(option.amountLabel || "") +
          "</strong><span>" +
          escapeHtml(option.description || "") +
          "</span>";
        donationCards.appendChild(card);
      });
    }

    function applyConfig() {
      document.title = (config.brandName || "Konticode") + " Support and Feedback";

      if (supportHeadline && config.supportHeadline) {
        supportHeadline.textContent = config.supportHeadline;
      }

      if (supportNote && config.supportNote) {
        supportNote.textContent = config.supportNote;
      }

      if (feedbackPage) {
        feedbackPage.value = window.location.href;
      }

      renderDonationCards();
    }

    function setStatus(message, type) {
      if (!feedbackStatus) {
        return;
      }

      feedbackStatus.textContent = message;
      feedbackStatus.className = "status" + (type ? " " + type : "");
    }

    function setCheckoutStatus(message, type) {
      if (!checkoutStatus) {
        return;
      }

      checkoutStatus.textContent = message;
      checkoutStatus.className = "status" + (type ? " " + type : "");
    }

    function getFocusableElements() {
      if (!feedbackModal) {
        return [];
      }

      return Array.from(feedbackModal.querySelectorAll(focusableSelector)).filter(function (element) {
        return !element.hidden;
      });
    }

    function openFeedback() {
      if (!feedbackModal) {
        return;
      }
      successfulSubmissionsThisOpen = 0;
      const feedbackBackdrop = document.getElementById("feedback-backdrop");
      lastFocusedElement = document.activeElement;
      feedbackModal.removeAttribute("hidden");
      feedbackModal.setAttribute("aria-hidden", "false");
      if (feedbackBackdrop) {
        feedbackBackdrop.removeAttribute("hidden");
      }
      document.body.style.overflow = "hidden";

      window.setTimeout(function () {
        const focusableElements = getFocusableElements();
        if (focusableElements.length) {
          focusableElements[0].focus();
        }
      }, 0);
    }

    function closeFeedback() {
      if (!feedbackModal) {
        return;
      }
      if (closeTimerId) {
        window.clearTimeout(closeTimerId);
        closeTimerId = null;
      }
      const feedbackBackdrop = document.getElementById("feedback-backdrop");
      feedbackModal.setAttribute("hidden", "");
      feedbackModal.setAttribute("aria-hidden", "true");
      if (feedbackBackdrop) {
        feedbackBackdrop.setAttribute("hidden", "");
      }
      document.body.style.overflow = "";
      setStatus("", "");

      if (resetFormOnClose) {
        resetFeedbackForm();
        resetFormOnClose = false;
      }

      if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {
        lastFocusedElement.focus();
      }
    }

    function trapFocus(event) {
      if (event.key !== "Tab" || !feedbackModal || feedbackModal.hasAttribute("hidden")) {
        return;
      }

      const focusableElements = getFocusableElements();

      if (!focusableElements.length) {
        return;
      }

      const first = focusableElements[0];
      const last = focusableElements[focusableElements.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
        return;
      }

      if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    function validate(formData) {
      if (!formData.get("topic")) {
        return "Choose a topic so the message gets routed correctly.";
      }

      if (!formData.get("email")) {
        return "Add an email address so we can follow up if needed.";
      }

      if (!formData.get("message")) {
        return "Please include a short message.";
      }

      return "";
    }

    function buildPayload(formData) {
      return {
        topic: formData.get("topic"),
        email: formData.get("email"),
        message: formData.get("message"),
        followUp: Boolean(formData.get("followUp")),
        page: formData.get("page"),
        submittedAt: new Date().toISOString(),
        source: config.brandName || "Konticode"
      };
    }

    function sendViaEmail(payload) {
      const subject = encodeURIComponent("Konticode feedback: " + payload.topic);
      const body = encodeURIComponent(
        [
          "Topic: " + payload.topic,
          "Email: " + payload.email,
          "Follow up: " + (payload.followUp ? "Yes" : "No"),
          "Page: " + payload.page,
          "",
          payload.message
        ].join("\n")
      );

      window.location.href =
        "mailto:" + (feedbackConfig.emailFallback || "") + "?subject=" + subject + "&body=" + body;
    }

    function resetFeedbackForm() {
      if (feedbackForm) {
        feedbackForm.reset();
      }

      if (feedbackPage) {
        feedbackPage.value = window.location.href;
      }
    }

    async function startCheckout(plan, triggerButton) {
      if (!config.checkoutEndpoint) {
        setCheckoutStatus("Stripe checkout is not configured yet.", "error");
        return;
      }

      const originalText = triggerButton ? triggerButton.textContent : "";
      if (triggerButton) {
        triggerButton.disabled = true;
        triggerButton.textContent = "Redirecting...";
      }
      setCheckoutStatus("Opening secure checkout...", "loading");

      try {
        const response = await fetch(config.checkoutEndpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ plan: plan })
        });
        const data = await response.json();

        if (!response.ok || !data.url) {
          throw new Error(data.error || "Checkout could not be started.");
        }

        window.location.href = data.url;
      } catch (error) {
        setCheckoutStatus(error.message || "Checkout could not be started.", "error");
        if (triggerButton) {
          triggerButton.disabled = false;
          triggerButton.textContent = originalText;
        }
      }
    }

    async function submitFeedback(event) {
      if (!feedbackForm || !feedbackSubmit) {
        return;
      }

      event.preventDefault();

      if (successfulSubmissionsThisOpen >= 3) {
        setStatus("We are reviewing your message, Thank you for your time and support.", "success");
        return;
      }

      const formData = new FormData(feedbackForm);
      const validationMessage = validate(formData);

      if (validationMessage) {
        setStatus(validationMessage, "error");
        return;
      }

      const payload = buildPayload(formData);
      feedbackSubmit.disabled = true;
      setStatus("Sending your feedback...", "");

      try {
        if (feedbackConfig.endpoint) {
          const response = await fetch(feedbackConfig.endpoint, {
            method: feedbackConfig.method || "POST",
            headers: feedbackConfig.headers || {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
          });

          if (!response.ok) {
            throw new Error("Feedback endpoint returned " + response.status);
          }

          resetFeedbackForm();
          successfulSubmissionsThisOpen += 1;
          setStatus(feedbackConfig.successMessage || "Thanks for the note.", "success");
          resetFormOnClose = true;
          closeTimerId = window.setTimeout(function () {
            closeFeedback();
          }, 1200);
          return;
        }

        sendViaEmail(payload);
        resetFeedbackForm();
        successfulSubmissionsThisOpen += 1;
        setStatus(
          successfulSubmissionsThisOpen > 1
            ? "Your email has been sent, Thank you once again for your feedback!!"
            : "Your email has been sent, Thank you for your feedback!!",
          "success"
        );
      } catch (error) {
        setStatus("Feedback could not be delivered. Check your endpoint settings and try again.", "error");
      } finally {
        feedbackSubmit.disabled = false;
      }
    }

    openButtons.forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        openFeedback();
      });
    });

    closeButtons.forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        closeFeedback();
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && feedbackModal && !feedbackModal.hasAttribute("hidden")) {
        event.preventDefault();
        closeFeedback();
        return;
      }

      trapFocus(event);
    });

    if (feedbackForm) {
      feedbackForm.addEventListener("submit", submitFeedback);
    }

    if (donateLink) {
      donateLink.addEventListener("click", function () {
        startCheckout(selectedDonationPlan, donateLink);
      });
    }

    if (monthlyLink) {
      monthlyLink.addEventListener("click", function () {
        startCheckout(config.monthlyPlan || "monthly_support", monthlyLink);
      });
    }

    applyConfig();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFeedbackWidget);
  } else {
    initFeedbackWidget();
  }
})();
