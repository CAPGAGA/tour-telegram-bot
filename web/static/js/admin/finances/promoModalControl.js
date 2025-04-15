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
                if (rout.is_displayed == true) {
                    const label = document.createElement('label')
                    label.className = 'checkbox-item';

                    const checkBox = document.createElement('input')
                    checkBox.value = rout.id;
                    checkBox.id = 'promo-rout-' + rout.id;
                    checkBox.name = 'promo-rout';
                    checkBox.type = 'checkbox';

                    label.appendChild(checkBox);
                    label.innerHTML += rout.rout_name;
                    checkBoxList.appendChild(label);
                };
            });
        })
        .catch(error => showMessage(error, "error"));
    document.getElementById('createPromoBtn').innerHTML = 'Create Promo';
    document.getElementById('createPromoBtn').setAttribute('data-action', 'create')
    document.getElementById('promoModal').style.display = 'flex';
});

document.getElementById('closePromoModal').addEventListener('click', () => {
    getPromosList();
    document.getElementById('promoModal').style.display = 'none';
    document.getElementById('promoForm').reset();
    document.getElementById('checkbox-list').innerHTML = '';
});

export function openPromoEdit(promoId) {
    const creatorId = document.getElementById("username").getAttribute("data-creator-id");

    // Fetch both promo details and creator's routs
    Promise.all([
        fetch(`/apiV1/promo/get-promo?promo_id=${promoId}`).then(res => res.json()),
        fetch(`/apiV1/creator_rout/get-creator-rout?creator_id=${creatorId}`).then(res => res.json())
    ])
    .then(([promoData, routData]) => {
        const promo = promoData;
        const routs = routData.routs;
        const checkBoxList = document.getElementById('checkbox-list');

        // Fill form fields
//        document.getElementById('promo-id').value = promo.id;
        document.getElementById('promo-code').value = promo.code;
        document.getElementById('promo-type').value = promo.promo_type;
        document.getElementById('promo-discount').value = promo.discount;
        document.getElementById('promo-start').value = promo.promo_start.slice(0, 10);
        document.getElementById('promo-end').value = promo.promo_end.slice(0, 10);
        document.getElementById('promo-limit').value = promo.use_limit;

        // Inject rout checkboxes
        checkBoxList.innerHTML = '';
        routs.forEach(rout => {
            const label = document.createElement('label');
            label.className = 'checkbox-item';

            const checkBox = document.createElement('input');
            checkBox.type = 'checkbox';
            checkBox.name = 'promo-rout';
            checkBox.id = 'promo-rout-' + rout.id;
            checkBox.value = rout.id;
            console.log(promo.routs)
            console.log(rout.id)
            console.log(promo.routs.includes(rout.id))

            label.appendChild(checkBox);
            label.innerHTML += rout.rout_name;
            checkBoxList.appendChild(label);

            if (promo.routs.includes(rout.id)) {
                document.getElementById('promo-rout-' + rout.id).checked = true;
            }
        });

        // Show modal
        document.getElementById('createPromoBtn').innerHTML = 'Edit Promo';
        document.getElementById('createPromoBtn').setAttribute('data-action', 'edit')
        document.getElementById('createPromoBtn').setAttribute('data-promo-id', promo.id)
        document.getElementById('promoModal').style.display = 'flex';
    })
    .catch(error => showMessage(error.message || "Failed to fetch promo details", "error"));
}
