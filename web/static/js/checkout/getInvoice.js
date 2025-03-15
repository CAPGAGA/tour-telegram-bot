import { showMessage } from "../revolver.js";

document.addEventListener("DOMContentLoaded", function () {
    const payButton = document.getElementById("pay-with-paypal");

    const tourId = payButton.getAttribute("data-tour-id");
    const userId = payButton.getAttribute("data-user-id");

    if (!tourId) {
        showMessage("Invalid tour ID", 'error');
        return;
    }

    // PayPal Payment
    document.getElementById("pay-with-paypal").addEventListener("click", function () {

        fetch(`/apiV1/order/create/paypal`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: userId,
                rout_id: tourId
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.payment_link) {
                    window.location.href = data.payment_link; // Redirect to PayPal
                } else {
                    showMessage("Error processing PayPal payment", 'error');
                }
            })
            .catch(error =>showMessage("Payment failed", 'error'));
    });
});