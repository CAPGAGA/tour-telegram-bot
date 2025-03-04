import { showMessage } from "./revolver.js";

document.addEventListener("DOMContentLoaded", function () {
    const registerForm = document.querySelector("#register-form");

    registerForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const username = document.querySelector("#username").value;
        const password = document.querySelector("#password").value;

        const requestData = {
            username: username,
            password: password,
        };

        try {
            const response = await fetch("/apiV1/admin/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestData),
            });

            const data = await response.json();

            if (response.ok) {
                document.cookie = `auth_token=${data.token}; path=/; max-age=${data.expires_in}`;
                alert("User registered successfully! Redirecting...");
                showMessage("Success: " + "Registered user successfully! Redirecting...)", "success");
                window.location.href = "/tour-admin";
            } else if (response.status === 403) {
                showMessage("Error: " + data.detail, "error");
            } else if (response.status === 400) {
                showMessage("Info: " + data.detail, "info");
            } else {
                showMessage("Error: " + data.detail, "error");
            }
        } catch (error) {
            console.error("Error registering user:", error);
            showMessage("Error: " + "An error occurred. Please try again later.", "error");
        }
    });
});
