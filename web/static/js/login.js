import { showMessage } from "./revolver.js";

document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.querySelector("#login-form");

    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const username = document.querySelector("#username").value;
        const password = document.querySelector("#password").value;

        const requestData = {
            username: username,
            password: password,
        };

        try {
            const response = await fetch("/apiV1/admin/crm-login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestData),
            });

            const data = await response.json();

            if (response.ok) {
                document.cookie = `auth_token=${data.token}; path=/; max-age=${data.expires_in}`;
                showMessage("Login successful! Redirecting...", "success");
                setTimeout(() => { window.location.href = "/tour-admin"; }, 2000);
            } else if (response.status === 403) {
                showMessage("Error: " + data.detail, "error");
            } else if (response.status === 400) {
                showMessage("Warning: " + data.detail, "info");
            } else {
                showMessage("Error: " + data.detail, "error");
            }
        } catch (error) {
            console.error("Error logging in:", error);
            showMessage("An error occurred. Please try again later.", "error");
        }
    });
});