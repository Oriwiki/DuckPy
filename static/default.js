var title = $('#title').text();


$('#diffbtn').click(function() {
    var oldrev = $('input[name=oldrev]:checked').val();
    var rev = $('input[name=rev]:checked').val();
    
    if (oldrev && rev) {
        location.href = '/diff/' + encodeURI(title) + '?rev=' + rev + '&oldrev=' + oldrev;
    }
    
});