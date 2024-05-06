$(document).ready(function(){
    const addRoutBtn = $('#add-rout-btn');
    const addRoutPointBtn = $('#add-rout-point-btn');
    const allRoutsTableBtn = $('#show-rout-btn');
    const allRoutPointsTableBtn = $('show-rout-points-btn');

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



})