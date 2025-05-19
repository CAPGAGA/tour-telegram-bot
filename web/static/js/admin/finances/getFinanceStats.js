import { showMessage } from "../../revolver.js";

export function fetchCreatorFinancesStats() {
     fetch('/apiV1/creator_rout/get-creators-stats')
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch stats");
            return response.json();
        })
        .then(data => {
            document.getElementById('finances-metric-balance').textContent = `${data.total_balance} $`;
            document.getElementById('finances-metric-withdraw').textContent = `${data.withdrawals} $`;

        })
        .catch(error => {
            showMessage(error.message, "error");
        });
}