import { showMessage } from "../../revolver.js";
import { getPromosList } from "./getPromosList.js";

export function deactivatePromo(promoId) {
    fetch(`/apiV1/promo/deactivate-promo?promo_id=${promoId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        }
    )
        .then(response => response.json())
        .then(data => {
            showMessage(data.message, "success");
            getPromosList();
        })
        .catch(error => showMessage(error, "error"));
}
