import { showMessage } from "../revolver.js";

document.addEventListener("DOMContentLoaded", function () {
    // Get forms and buttons for switching between forms
    const userBtn = document.getElementById("user-btn");
    const creatorBtn = document.getElementById("creator-btn");
    const userForm = document.getElementById("user-form");
    const creatorForm = document.getElementById("creator-form");
    const loginForm = document.getElementById("login-form");

    // Toggle Forms
    if (userBtn){
        userBtn.addEventListener("click", () => {
            userForm.style.display = "block";
            creatorForm.style.display = "none";
            userBtn.classList.add("is-light");
            creatorBtn.classList.remove("is-light");
        });
    }

    if (creatorBtn) {
        creatorBtn.addEventListener("click", () => {
            userForm.style.display = "none";
            creatorForm.style.display = "block";
            creatorBtn.classList.add("is-light");
            userBtn.classList.remove("is-light");
        });
    }


    // Handle User Registration
    if (userForm) {
        document.getElementById("register-user").addEventListener("submit", function (event) {
            event.preventDefault();

            const username = document.getElementById("user-username").value.trim();
            const password = document.getElementById("user-password").value.trim();

            if (!username || !password) {
                showMessage("Please fill in all fields!", "error");
                return;
            }

            const requestData = { username, password };

            fetch("/apiV1/auth/register-user", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(({ status, body }) => {
                if (status !== 200) {
                    throw new Error(body.detail || "Failed to register.");
                }
                showMessage("User registered successfully!", "success");
                setTimeout(() => window.location.href = "/login", 1500);
            })
            .catch(error => showMessage(error.message, "error"));
        });

    }


    // Handle Admin (Creator) Registration
    if (creatorForm) {
        document.getElementById("register-creator").addEventListener("submit", function (event) {
            event.preventDefault();

            const username = document.getElementById("creator-username").value.trim();
            const password = document.getElementById("creator-password").value.trim();

            if (!username || !password) {
                showMessage("Please fill in all fields!", "error");
                return;
            }

            const requestData = { username, password };

            fetch("/apiV1/auth/register-admin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(({ status, body }) => {
                if (status !== 200) {
                    throw new Error(body.detail || "Failed to register.");
                }
                showMessage("Creator registered successfully!", "success");
                setTimeout(() => window.location.href = "/login", 1500);
            })
            .catch(error => showMessage(error.message, "error"));
        });
    }


    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();

            if (!username || !password) {
                showMessage("Please enter both username and password.", "error");
                return;
            }

            const requestData = { username, password };

            fetch("/apiV1/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData),
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(({ status, body }) => {
                if (status !== 200) {
                    throw new Error(body.detail || "Login failed.");
                }

                // Store JWT token in cookies
                document.cookie = `auth_token=${body.token}; path=/; max-age=${7 * 24 * 60 * 60}; Secure`;

                showMessage("Login successful!", "success");

                // Redirect users & admins
                setTimeout(() => {
                    if (body.is_admin) {
                        window.location.href = "/tour-admin";
                    } else {
                        window.location.href = "/shop";
                    }
                }, 1500);
            })
            .catch(error => showMessage(error.message, "error"));
        });
    }

});