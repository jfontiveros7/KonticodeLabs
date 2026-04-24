window.KONTICODE_CONFIG = {
  brandName: "Konticode",
  supportHeadline: "Support Konticode",
  supportNote: "Contributions help fund development time, hosting, and polished releases.",
  donationOptions: [
    {
      plan: "donation_5",
      amountLabel: "$5",
      description: "Buy a coffee for late-night bug fixing."
    }
  ],
  checkoutEndpoint: "/api/create-checkout-session",
  monthlyPlan: "monthly_support",
  feedback: {
    endpoint: "/api/feedback",
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    emailFallback: "contact@konticode.com",
    successMessage: "Thanks for the note. We read every submission."
  }
};
