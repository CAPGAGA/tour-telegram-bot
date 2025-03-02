function logoutUser() {
    fetch('/apiV1/admin/logout', { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            document.cookie = "auth_token=; path=/; max-age=0"; // Clear auth token manually
            window.location.href = "/login"; // Redirect to login page
        })
        .catch(error => console.error("Logout failed:", error));
}

document.addEventListener("DOMContentLoaded", function () {
    let logoutBtn = document.querySelector("#logout");

    if (logoutBtn) {
        logoutBtn.addEventListener("click", logoutUser);
    }
});