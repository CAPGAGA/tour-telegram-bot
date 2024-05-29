$(document).ready(function(){
    const addRoutBtn = $('#add-rout-btn');
    const addRoutPointBtn = $('#add-rout-point-btn');
    const allRoutsTableBtn = $('#show-rout-btn');
    const allRoutPointsTableBtn = $('#show-rout-points-btn');
    const allUsersBtn = $('#show-users-btn');
    const addPromoBtn = $('#add-promo-btn');
    const allPromosBtn = $('#show-promo-btn');

    $('.form-wrapper').hide();

    addRoutBtn.on('click', function(){
        $('.form-wrapper').hide();
        $('#add-rout-wrapper').show();
    })

    allRoutsTableBtn.on('click', function(){
        const tableRouts = $('#all-rout-table')
        tableRouts.find('.table-row').remove();

        $.ajax({
            url: `/routs/`,
            method: 'GET',
            success: function(data) {
                data.forEach(function(rout){
                    tableRouts.append(
                        `
                            <tr class="table-row">
                                <td class="table-cell data">${rout.id}</td>
                                <td class="table-cell data">${rout.rout_name}</td>
                                <td class="table-cell data">
                                  <button class="base-btn edit" data-rout-id="${rout.id}">Редактировать</button>
                                  <button class="base-btn delete" data-rout-id="${rout.id}">Удалить</button>
                                </td>
                            </tr>
                        `
                    )
                })

                $('.base-btn.delete').on('click', function(){
                    $.ajax({
                        url: `/routs/${$(this).data('rout-id')}`,
                        method: 'DELETE',
                        success: function(data) {
                            alert('Удален маршрут: ' + data.deleted)
                            allRoutsTableBtn.click();
                        },
                        error: function(error){
                            console.log(error)
                            alert('Ошибка')
                        }
                    })
                });
                $('.base-btn.edit').on('click', function(){
                    const prevValue = $(this).parent().prev().text();


                    $(this).parent().prev().text('')
                    $(this).parent().prev().append(`<input type="text" class="form-input" name="description" id='temp-name-input' placeholder='Земун' value="${prevValue}">`)
                    $(this).text('Сохранить').off('click').on('click', function(){

                        const newValue = $(this).parent().prev().find('#temp-name-input').val();
                        const routId = $(this).data('rout-id');

                        $.ajax({
                            url: `/routs/${routId}/${newValue}`,
                            method: 'PUT',
                            success: function(data) {
                                alert('Обновлён маршрут: ' + data.updated)
                                allRoutsTableBtn.click();
                            },
                            error: function(error){
                                console.log(error)
                                alert('Ошибка')
                            }
                        })

                        $(this).text('Редактировать')
                        $(this).parent().prev().text(newValue)
                        $(this).parent().prev().find('#temp-name-input').remove();

                    })
                })
            },
            error: function(error) {
                // Handle the error here
                console.log(error)
                alert('Ошибка')
            }
        });

        $('.form-wrapper').hide();
        $('#all-rout-wrapper').show();
    })

    addRoutPointBtn.on('click', function(){
        const routSelector = $('#rout')
        const routSelectorOptions = $("#rout").find('option')
        routSelectorOptions.remove();

        $.ajax({
            url: `/routs/`,
            method: 'GET',
            success: function(data) {
                data.forEach(function(rout){
                    routSelector.append(
                        `<option class="form-input" value="${rout.id}">${rout.rout_name}</option>`
                    )
                })
            },
            error: function(error) {
                // Handle the error here
                console.log(error)
                alert('Ошибка')
            }
        });

        $('.form-wrapper').hide();
        $('#add-rout-point-wrapper').show();
    })

    allRoutPointsTableBtn.on('click', function(){

        const tableRoutPoints = $('#all-rout-points-table')
        tableRoutPoints.find('.table-row').remove();

        $.ajax({
            url: `/rout-points/`,
            method: 'GET',
            success: function(data) {
                data.forEach(function(routPoint){
                    const images = routPoint.images
                    let imagesLinks = ''
                    if (images){
                        let buttonOffset = 0
                        imageNames = images.replaceAll('[', '').replaceAll(']', '').replaceAll("'", '').replaceAll(' ', '').split(',')
                        imageNames.forEach(function(imageName){
                            imagesLinks += `

                                <a href="/media/images/${imageName}" target="_blank">${imageName}</a>
                                <button type="button" class="table-del-btn" data-img-name="${imageName}" style="transform: translate(0px, ${buttonOffset}px)">X</button>

                            `
                            buttonOffset+=18;
                        })
                    };
                    tableRoutPoints.append(
                        `
                            <tr class="table-row data">
                                <td class="table-cell data">${routPoint.id}</td>
                                <td class="table-cell data">${routPoint.rout_id}</td>
                                <td class="table-cell data">${routPoint.description}</td>
                                <td class="table-cell data">${routPoint.map_point.replace('[', '').replace(']', '').replaceAll(' ', '').split(',')[0]}</td>
                                <td class="table-cell data">${routPoint.map_point.replace('[', '').replace(']', '').replaceAll(' ', '').split(',')[1]}</td>
                                <td class="table-cell data">${imagesLinks ? imagesLinks : ''}</td>
                                <td class="table-cell data"><a href="/media/audio/${routPoint.audio}" target="_blank">${routPoint.audio}</a></td>
                                <td class="table-cell data">
                                  <button class="base-btn edit" data-rout-point-id="${routPoint.id}">Редактировать</button>
                                  <button class="base-btn delete" data-rout-point-id="${routPoint.id}">Удалить</button>
                                </td>
                            </tr>
                        `
                    )
                })

                $('.base-btn.delete').on('click', function(){
                    routPointId = $(this).data('rout-point-id')
                    $.ajax({
                        url: `/rout-points/${routPointId}`,
                        method: 'DELETE',
                        success: function(data) {
                            alert('Удалена точка: ' + data.deleted);
                            allRoutPointsTableBtn.click();
                        },
                        error: function(error) {
                            alert('Ошибка')
                            console.log(error)
                        }
                    });
                });
                $('.base-btn.edit').on('click', function(){
//                  mapping table to consts
                    const routPointId = $(this).data('rout-point-id');
                    const descriptionCell = $(this).parent().prev().prev().prev().prev().prev();
                    const longCell = $(this).parent().prev().prev().prev().prev();
                    const latCell = $(this).parent().prev().prev().prev();
                    const imgCell = $(this).parent().prev().prev();
                    const audioCell = $(this).parent().prev();
//                  util vars
                    let toDeleteImgs = [];

//                  getting text and other values
                    let descriptionText = descriptionCell.text();
                    let longText = longCell.text();
                    let latText = latCell.text();

//                  getting rid off inner texts
                    descriptionCell.empty();
                    longCell.empty();
                    latCell.empty();

//                  appending inputs
                    descriptionCell.append(
                        `
                            <input type="text" class="form-input" name="description" id="rout-point-name-new" placeholder="Точка на улице X.Y" value="${descriptionText}">
                        `
                    );

                    longCell.append(
                        `
                            <input type="number" step="0.000000001" class="form-input" name="lon" id="rout-point-long-new" placeholder="44.123" value="${longText}">
                        `

                    );

                    latCell.append(
                        `
                            <input type="number" step="0.000000001" class="form-input" name="lat" id="rout-point-lat-new" placeholder="20.123" value="${latText}">
                        `

                    );

                    imgCell.append(
                        `
                            <input type="file" multiple class="form-input tall" name="images" id="rout-point-img-new" placeholder="">
                        `
                    );
                    imgCell.find('.table-del-btn').show();

                    imgCell.find('.table-del-btn').on('click', function(){

                        if (toDeleteImgs.includes($(this).data('img-name'))){
                            if (toDeleteImgs.length === 1){
                                toDeleteImgs.pop();
                                $(this).prev().children().unwrap();
                            }
                            else {
                                const elemIndex = toDeleteImgs.indexOf($(this).data('img-name'));
                                toDeleteImgs.splice(elemIndex, 1)
                                $(this).prev().children().unwrap();
                            }

                        }
                        else {
                            toDeleteImgs.push($(this).data('img-name'))
                            $(this).prev().wrap('<strike>');
                        }

                        console.log(toDeleteImgs)

                   })

                    audioCell.append(
                        `
                            <input type="file" class="form-input tall" name="audio" id="rout-point-audio-new" placeholder="">
                        `
                    );

                    $(this).text('Сохранить').off('click').on('click', function(){
                        const formData = new FormData();
                        let dataCollected = false;


                        const description = descriptionCell.find('input').val();
                        const lon = longCell.find('input').val();
                        const lat = latCell.find('input').val();


                        const images = imgCell.find('input').prop('files');
                        const audio = audioCell.find('input').prop('files');

                        console.log(images)
                        console.log(audio)

                        if (audio.length !== 0) {
                            formData.append('audio', audio[0]);
                            dataCollected = true
                        }


                        if (images.length !== 0) {
                            for (var i =0; i< images.length; i++) {
                                formData.append('images', images[i])
                            }
                            dataCollected = true
                        }

                        if (toDeleteImgs.length !== 0) {
                            formData.append('to_delete_imgs', toDeleteImgs)
                            dataCollected = true
                        }

                        for (var pair of formData.entries()) {
                            console.log(pair[0]+ ', ' + pair[1]);
                        }

                        $.ajax({
                            url: `/rout_points/?rout_point_id=${routPointId}&description=${description}&lon=${lon}&lat=${lat}&to_delete_imgs=${toDeleteImgs}`,
                            method: 'PUT',
                            data:  dataCollected ? formData : null,
                            processData: false,
                            contentType: false,
                            success: function(response, textStatus, xhr) {
                                console.log('Form submitted successfully');
                                alert('Отредактировано');
                                allRoutPointsTableBtn.click();
                            },
                            error: function(error) {
                              // Handle the error here
                                console.log(error)
                                alert('Ошибка')
                            }
                        });




                    })


                });


            },
            error: function(error) {
                alert('Ошибка')
                console.log(error)

            }
        });


        $('.form-wrapper').hide();
        $('#all-rout-points-wrapper').show();

    })

    allUsersBtn.on('click', function(){

        const allUsersTable = $('#all-users-table');
        allUsersTable.find('.table-row').remove();

        $.ajax({
            url: `/users/`,
            method: 'GET',
            success: function(data) {
                data.users.forEach(function(user){
                    allUsersTable.append(
                        `
                        <tr class="table-row data">
                            <td class="table-cell data">${user.id}</td>
                            <td class="table-cell data">${user.username}</td>
                            <td class="table-cell data">${user.access_granted ? "Да" : "Нет"}</td>
                            <td class="table-cell data">
                              <button class="base-btn edit" data-user-id="${user.id}">Дать доступ</button>
                              <button class="base-btn delete" data-user-id="${user.id}">Забрать доступ</button>
                            </td>
                        </tr>
                        `
                    )

                });
                $('.base-btn.edit').on('click', function(){
                    let userId = $(this).data("user-id");
                    $.ajax({
                        url: `/users-access/?user_id=${userId}`,
                        method: 'POST',
                        success: function(data) {
                         alert('Доступ выдан')
                         allUsersBtn.click()
                        },
                        error: function(error){
                          console.log(error)
                          alert('Ошибка')
                        }
                    });
                });

                $('.base-btn.delete').on('click', function(){
                    let userId = $(this).data("user-id");
                    $.ajax({
                        url: `/users-access/?user_id=${userId}`,
                        method: 'DELETE',
                        success: function(data) {
                         alert('Доступ забран')
                         allUsersBtn.click()
                        },
                        error: function(error){
                          console.log(error)
                          alert('Ошибка')
                        }
                    });
                });
            },
            error: function(error) {
                console.log(error)
            }
        });


        $('.form-wrapper').hide();
        $('#all-users-wrapper').show();
    })

    addPromoBtn.on('click', function(){
        $('.form-wrapper').hide();
        $('#add-promo-wrapper').show();
        $('#percent-wrapper').hide();
        $('#price-wrapper').hide();
    })

    allPromosBtn.on('click', function(){
        $('.form-wrapper').hide();
        const promosTable = $('#all-promo-table');
        promosTable.find('.table-row').remove();

        $.ajax({
            url: `/promo/?source=admin`,
            method: 'GET',
            success: function(data) {
                data.promos.forEach(function(promo){
                    promosTable.append(
                    `
                    <tr class="table-row data">
                        <td class="table-cell data">${promo.id}</td>
                        <td class="table-cell data">${promo.name}</td>
                        <td class="table-cell data">${promo.is_percent ? promo.percent : promo.price}${promo.is_percent ? '%' : 'руб.'}</td>
                        <td class="table-cell data">${promo.counter}</td>
                        <td class="table-cell data">${promo.promocode}</td>
                        <td class="table-cell data">
                          <button class="base-btn delete" data-promo-id="${promo.id}">Удалить</button>
                        </td>
                     </tr>
                    `
                    );
                })
                $('.base-btn.delete').on('click', function(){
                    let promoId = $(this).data("promo-id");
                    $.ajax({
                        url: `/promo/${promoId}`,
                        method: 'DELETE',
                        success: function(data) {
                         alert('Удалено')
                         allPromosBtn.click()
                        },
                        error: function(error){
                          console.log(error)
                          alert('Ошибка')
                        }
                    });
                });

            },
            error: function(error){
                console.log(error)
            }
        })

        $('#all-promo-wrapper').show();

    })


})