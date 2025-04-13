import { showMessage } from "../../revolver.js";
import { getPromosList } from "./getPromosList.js";

document.getElementById('openPromoModal').addEventListener('click', () => {
    // fetch creator's routs
    const creatorId = document.getElementById("username").getAttribute("data-creator-id");
    fetch(`/apiV1/creator_rout/get-creator-rout?creator_id=${creatorId}`)
        .then(response => response.json())
        .then(data => {
            const routs = data.routs;
            const checkBoxList = document.getElementById('checkbox-list');
            routs.forEach(rout => {
                // add route to select list in form
                const label = document.createElement('label')
                label.className = 'checkbox-item';

                const checkBox = document.createElement('input')
                checkBox.value = rout.id;
                checkBox.name = 'promo-rout';
                checkBox.type = 'checkbox';

                label.appendChild(checkBox);
                label.innerHTML += rout.rout_name;
                checkBoxList.appendChild(label);
            })
        })
        .catch(error => showMessage(error, "error"));
    document.getElementById('promoModal').style.display = 'flex';
});

document.getElementById('closePromoModal').addEventListener('click', () => {
    getPromosList();
    document.getElementById('promoModal').style.display = 'none';
    document.getElementById('promoForm').reset();
    document.getElementById('checkbox-list').innerHTML = '';
});
