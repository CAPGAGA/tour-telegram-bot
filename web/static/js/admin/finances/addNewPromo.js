import { showMessage } from "../../revolver.js";

document.getElementById('createPromoBtn').addEventListener('click', (e) => {
    e.preventDefault();

    const creatorId = document.getElementById("username").getAttribute("data-creator-id");
    const promoCode = document.getElementById('promo-code').value
    const promoType = document.getElementById('promo-type').value
    const promoDiscount = document.getElementById('promo-discount').value
    const promoStart = document.getElementById('promo-start').value
    const promoEnd = document.getElementById('promo-end').value
    const promoUseLimit = document.getElementById('promo-limit').value


    // validate form
    let routIds = [];
    const routCheckBoxes = document.getElementsByName('promo-rout');
    // get selected routs
    routCheckBoxes.forEach(rout => {
        if (rout.checked) {
            routIds.push(rout.value)
        }
    })

    if (!promoCode) {
        showMessage('Invalid Promo Code name', 'info')
        return
    }

    if (!promoType) {
        showMessage('Invalid Promo Type', 'info')
        return
    }

    if (!promoDiscount || promoDiscount <= 0 || promoDiscount > 100 && promoType === 'percent') {
        showMessage('Invalid Discount Value', 'info')
        return
    }

    if (routIds.length === 0) {
        showMessage('Select at least 1 rout', 'info')
        return
    }

    if (!promoStart && !promoEnd) {
        showMessage('Wrong dates of promo', 'info')
        return
    }

    if (!promoStart && !promoEnd && !promoUseLimit) {
        showMessage('Promo must have start date, end date or use limit', 'info')
        return
    }

    const requestData = {
        creator_id: creatorId,
        code: promoCode,
        promo_type: promoType,
        discount: promoDiscount,
        promo_start: promoStart,
        promo_end: promoEnd,
        use_limit: promoUseLimit,
        routs: routIds
    }

    fetch("/apiV1/promo/create", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (response.status !== 200) {
            showMessage('Error creating promo', 'error')
        }
        document.getElementById('closePromoModal').click();
    })
    .catch(
        error => console.error("Error while adding promo:", error)
    )
})
