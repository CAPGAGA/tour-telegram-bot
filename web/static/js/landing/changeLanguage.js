document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".change-lang").forEach(button => {
        button.addEventListener("click", function () {
            const selectedLang = this.getAttribute("data-lang");

            fetch(`/apiV1/user/set-language/${selectedLang}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ lang: selectedLang })
            })
            .then(response => response.json())
            .then(data => {
                console.log("Language changed to:", data.lang);
                location.reload(); // Reload to apply new language
            })
            .catch(error => console.error("Error changing language:", error));
        });
    });
});