import { showMessage } from "../../revolver.js";

export function getPromosList() {
    // get creator's promo list
    const creatorId = document.getElementById("username").getAttribute("data-creator-id");
    const promoContainer = document.getElementById('promo-list');
    promoContainer.innerHTML = '';

    fetch(`/apiV1/promo/get?creator_id=${creatorId}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(promo => {
                const promoCard = document.createElement('div')
                if (promo.active) {
                    promoCard.className = 'promo-card';
                } else {
                    promoCard.className = 'promo-card inactive'
                }
                const promoInfo =  document.createElement('div')
                promoInfo.className = 'promo-info';
                promoInfo.innerHTML = `
                    <strong>${promo.code}</strong>
                    <br>
                    ${promo.promo_type} discount of ${promo.discount}
                    <br>
                    Valid until ${promo.promo_end}
                `
                promoCard.appendChild(promoInfo)
                promoContainer.appendChild(promoCard)
                const promoActions = document.createElement('div')
                promoActions.className = 'promo-actions'
                let buttons = ''
                if (promo.active) {
                    buttons = `
                        <button class="edit-promo" data-promo-id="${promo.id}">Edit</button>
                        <button class="deactivate-promo" data-promo-id="${promo.id}">Deactivate</button>
                    `
                } else {
                    buttons = `
                        <button class="edit-promo" data-promo-id="${promo.id}">Edit</button>
                    `
                }
                promoActions.innerHTML = buttons
                promoCard.appendChild(promoActions)

            })
        })
        .catch(error => showMessage(error, "error"));
}
