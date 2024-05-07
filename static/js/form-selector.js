$(document).ready(function(){
    const addRoutBtn = $('#add-rout-btn');
    const addRoutPointBtn = $('#add-rout-point-btn');
    const allRoutsTableBtn = $('#show-rout-btn');
    const allRoutPointsTableBtn = $('#show-rout-points-btn');

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

        console.log(routSelectorOptions)
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
                    const imagesLinks = []
                    if (images){
                        imageNames = images.replace('[', '').replace(']', '').replaceAll("'", '').split(',')
                        console.log(imageNames)
                        imageNames.forEach(function(imageName){
                            console.log(imageName)
                            imagesLinks.push(`<a href="/media/images/${imageName}" target="_blank">${imageName}</a>`)
                        })
                    };
                    tableRoutPoints.append(
                        `
                            <tr class="table-row data">
                                <td class="table-cell data">${routPoint.id}</td>
                                <td class="table-cell data">${routPoint.rout_id}</td>
                                <td class="table-cell data">${routPoint.description}</td>
                                <td class="table-cell data">${routPoint.map_point.replace('[', '').replace(']', '').split(',')[0]}</td>
                                <td class="table-cell data">${routPoint.map_point.replace('[', '').replace(']', '').split(',')[1]}</td>
                                <td class="table-cell data">${imagesLinks ? imagesLinks : None}</td>
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

            },
            error: function(error) {


            }
        });


        $('.form-wrapper').hide();
        $('#all-rout-points-wrapper').show();

    })



})