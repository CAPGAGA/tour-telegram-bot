import { showMessage } from "../../revolver.js";
import { openPromoEdit } from "./promoModalControl.js"
import { deactivatePromo } from "./deactivatePromo.js"

export function getPromosList() {
    // get creator's promo list
    const creatorId = document.getElementById("username").getAttribute("data-creator-id");
    const promoContainer = document.getElementById('promo-list');
    promoContainer.innerHTML = '';

    fetch(`/apiV1/promo/get-all?creator_id=${creatorId}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(promo => {
                const promoCard = document.createElement('div');
                promoCard.className = promo.active ? 'promo-card' : 'promo-card inactive';

                const promoInfo = document.createElement('div');
                promoInfo.className = 'promo-info';
                let discount = promo.promo_type === 'flat' ? `${promo.discount}$` : `${promo.discount}%`;
                promoInfo.innerHTML = `
                    <strong>${promo.code}</strong><br>
                    ${promo.promo_type} discount of ${discount}<br>
                    Valid until ${promo.promo_end}
                `;

                const promoActions = document.createElement('div');
                promoActions.className = 'promo-actions';

                const editBtn = document.createElement('button');
                editBtn.className = 'edit-promo';
                editBtn.textContent = 'Edit';
                editBtn.setAttribute('data-promo-id', promo.id);
                editBtn.addEventListener('click', () => openPromoEdit(promo.id));

                promoActions.appendChild(editBtn);

                if (promo.active) {
                    const deactivateBtn = document.createElement('button');
                    deactivateBtn.className = 'deactivate-promo';
                    deactivateBtn.textContent = 'Deactivate';
                    deactivateBtn.setAttribute('data-promo-id', promo.id);

                    promoActions.appendChild(deactivateBtn);
                    deactivateBtn.addEventListener('click', () => deactivatePromo(promo.id));
                }

                promoCard.appendChild(promoInfo);
                promoCard.appendChild(promoActions);
                promoContainer.appendChild(promoCard);
            });
        })
        .catch(error => showMessage(error, "error"));
}
