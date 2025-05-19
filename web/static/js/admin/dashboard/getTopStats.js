import { showMessage } from "../../revolver.js";

export function fetchCreatorTopStats() {
     fetch('/apiV1/creator_rout/get-creators-stats')
        .then(response => {
            if (!response.ok) throw new Error("Failed to fetch stats");
            return response.json();
        })
        .then(data => {
            document.getElementById('metric-balance').textContent = `${data.total_balance} $`;
            document.getElementById('metric-orders').textContent = data.total_orders;
            document.getElementById('metric-clients').textContent = data.unique_clients;
            document.getElementById('metric-tours').textContent = data.active_tours;
        })
        .catch(error => {
            showMessage(error.message, "error");
        });
}