$(document).ready(function(){
    const addRoutSubmit = $('#add-rout-submit');

    addRoutSubmit.on('click', function(e){
        e.preventDefault();

        let routName = $('#rout-name').val();

        $.ajax({
          type: 'POST',
          url: '/routs/' + routName,
          success: function(response) {
            console.log('Form submitted successfully');
            alert('Добавлено')
            $('#add-rout-btn').click()
          },
          error: function(error) {
            console.log(error)
            alert('Ошибка')
          }
        });
    })

    const addRoutPointBtn = $('#add-rout-point-submit');

    addRoutPointBtn.on('click', function(e){
        e.preventDefault();

        const formData = new FormData();
        let dataCollected = false;

        const rout_id =  $('#rout').find(":selected").val();
        const description = $('#rout-point-name').val();
        const lon = $('#rout-point-long').val();
        const lat = $('#rout-point-lat').val();


        const images = $('#rout-point-img').prop('files');
        const audio = $('#rout-point-audio').prop('files');

        if (audio.length !== 0) {
            formData.append('audio', audio[0]);
            dataCollected = true
        }


        if (images.length !== 0) {
            for (var i =0; i<$('#rout-point-img')[0].files.length; i++) {
                formData.append('images', $('#rout-point-img').prop('files')[i])
            }
            dataCollected = true
        }


        for (var pair of formData.entries()) {
            console.log(pair[0]+ ', ' + pair[1]);
        }

        $.ajax({
            url: `/rout_points/?rout_id=${rout_id}&description=${description}&lon=${lon}&lat=${lat}`,
            method: 'POST',
            data:  dataCollected ? formData : null,
            processData: false,
            contentType: false,
            success: function(response, textStatus, xhr) {
                console.log('Form submitted successfully');
                alert('Добавлено');
                $('#add-rout-point-btn').click();
            },
            error: function(error) {
              // Handle the error here
                console.log(error)
                alert('Ошибка')
            }
        });

    })

    const promoTypeSwitcher = $('#promo-type');

    promoTypeSwitcher.on('change', function(){
        if($(this).find('.form-input:selected').val() === '1'){
            $('#percent-wrapper').hide().find('.form-input').val('');
            $('#price-wrapper').show().find('.form-input').val('');
        }
        else {
            $('#percent-wrapper').show().find('.form-input').val('');
            $('#price-wrapper').hide().find('.form-input').val('');
        }
    })

    const submitPromo = $('#add-promo-submit');

    submitPromo.on('click', function(e){

        e.preventDefault();
        let URL = `/promo/`

        const promoName = $('#promo-name').val();
        const promoPercent = $('#promo-percent').val();
        const promoPrice = $('#promo-price').val();
        const promoPhrase = $('#promo-phrase').val();
        const promoCounter = $('#promo-counter').val();

        URL = URL + `?name=${promoName}`
        if(promoPercent){
            URL = URL + `&percent=${promoPercent}`
        }
        if (promoPrice){
            URL = URL + `&price=${promoPrice}`
        }
        if (promoPhrase){
            URL = URL + `&phrase=${promoPhrase}`
        }
        if (promoCounter) {
            URL = URL + `&counter=${promoCounter}`
        }
//      `/promo/?name=${promoName}&phrase=${promoPhrase}&price=${promoPrice}&percent=${promoPercent}&counter=${promoCounter}`
        $.ajax({
            url: URL,
            method: 'POST',
            processData: false,
            contentType: false,
            success: function(response, textStatus, xhr) {
                console.log('Form submitted successfully');
                alert('Добавлено');
            },
            error: function(error) {
              // Handle the error here
                console.log(error)
                alert('Ошибка')
            }
        });
    })

})