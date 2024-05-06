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

        const rout_id =  $('#rout').find(":selected").val();
        const description = $('#rout-point-name').val();
        const lon = $('#rout-point-long').val();
        const lat = $('#rout-point-lat').val();


        const images = $('#rout-point-img').prop('files');
        const audio = $('#rout-point-audio').prop('files');

        formData.append('audio', audio[0]);
        for (var i =0; i<$('#rout-point-img')[0].files.length; i++) {
            formData.append('images', $('#rout-point-img').prop('files')[i])
        }

        for (var pair of formData.entries()) {
            console.log(pair[0]+ ', ' + pair[1]);
        }


        $.ajax({
            url: `/rout_points/?rout_id=${rout_id}&description=${description}&lon=${lon}&lat=${lat}`,
            method: 'POST',
            data: formData,
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

})