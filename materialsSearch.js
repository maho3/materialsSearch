
function addQuerySet(set){
    var queries = document.getElementById("queries");
    if (set.checked){
        switch(set.value){
            case "sulfides":
                str=''
                for (var i=0; i<sulfides.length;i++){
                    str += sulfides[i]+'; ';
                } queries.value += str;
                break;
            case "selenides":
                str=''
                for (var i=0; i<selenides.length;i++){
                    str += selenides[i]+'; ';
                } queries.value += str;
                break;
            case "twoMetals":
                str=''
                for (var i=0; i<twoMetals.length;i++){
                    str += twoMetals[i]+'; ';
                } queries.value += str;
                break;
            case "oxides":
                str=''
                for (var i=0; i<oxides.length;i++){
                    str += oxides[i]+'; ';
                } queries.value += str;
                break;
            case "vanadates":
                str=''
                for (var i=0; i<vanadates.length;i++){
                    str += vanadates[i]+'; ';
                } queries.value += str;
                break;
        }
    } else {
        switch(set.value){
            case "sulfides":
                for (var i=0; i<sulfides.length; i++){
                    queries.value = queries.value.replace(sulfides[i]+'; ',"");
                }break;
            case "selenides":
                for (var i=0; i<selenides.length; i++){
                    queries.value = queries.value.replace(selenides[i]+'; ',"");
                }break;
            case "twoMetals":
                for (var i=0; i<twoMetals.length; i++){
                    queries.value = queries.value.replace(twoMetals[i]+'; ',"");
                }break;
            case "oxides":
                for (var i=0; i<oxides.length; i++){
                    queries.value = queries.value.replace(oxides[i]+'; ',"");
                }break;
            case "vanadates":
                for (var i=0; i<vanadates.length; i++){
                    queries.value = queries.value.replace(vanadates[i]+'; ',"");
                }break;
        }

    }
}

function resetKeyDefault(){
    document.getElementById("keywords").value=''
    for (var i = 0; i<keywords.length; i++) {
        document.getElementById("keywords").value += keywords[i] + '; ';
    }
}

function sumPerm(){
    var atext = $('#permtextA').val().split(", ");
    var btext = $('#permtextB').val().split(", ");
    var ctext = $('#permtextC').val().split(", ");
    var dtext = $('#permtextD').val().split(", ");

    atext = $.grep(atext, function(a) {
        return a != '';
    });
    btext = $.grep(btext, function(a) {
        return a != '';
    });
    ctext = $.grep(ctext, function(a) {
        return a != '';
    });
    dtext = $.grep(dtext, function(a) {
        return a != '';
    });

    var resString = ''

    if (atext.length != 0) {
        resString += '[' + atext.join() + ']';
    }
    if (btext.length != 0) {
        resString += '[' + btext.join() + ']';
    }
    if (ctext.length != 0) {
        resString += '[' + ctext.join() + ']';
    }
    if (dtext.length != 0) {
        resString += '[' + dtext.join() + ']';
    }

    $('#permsum').val(resString);
}

function expand(change, id){
    if (change == 'full') {
        console.log(id);
        $('#mp' + id + '_con').show();
        $('#wok' + id + '_con').show();
        $('#mp' + id + '_full').hide();
        $('#wok' + id + '_full').hide();
    } else {
        $('#mp' + id + '_con').hide();
        $('#wok' + id + '_con').hide();
        $('#mp' + id + '_full').show();
        $('#wok' + id + '_full').show();
    }
}

function hoveron(id){
    $('#wok' + id + '_con').addClass('highlight');
    $('#mp' + id + '_con').addClass('highlight');

    $('#mp' + id + '_full').removeClass('selected');
    $('#wok' + id + '_full').removeClass('selected');
    $('#mp' + id + '_full').addClass('highlightselected');
    $('#wok' + id + '_full').addClass('highlightselected');

}
function hoveroff(id){
    $('#wok' + id + '_con').removeClass('highlight');
    $('#mp' + id + '_con').removeClass('highlight');

    $('#mp' + id + '_full').removeClass('highlightselected');
    $('#wok' + id + '_full').removeClass('highlightselected');
    $('#mp' + id + '_full').addClass('selected');
    $('#wok' + id + '_full').addClass('selected');
}

function sortby(type, search, elem){
    $('#serverstatus').empty().append('Generating sort...' + "&#13;&#10;");

    url = $('#ajaxform').attr( "action" );

    event.preventDefault();

    var uppresence = $(elem).text().includes('\u25b2')
    if (search == 'mp'){
        var sn = $('#mptitle').text();
        var pn = $('#woktitle').text()
    } else {
        var sn = $('#woktitle').text();
        var pn = $('#mptitle').text()
    }

    $.post(url,{
        searchtype:'sort',
        sortname:sn,
        partname:pn,
        sorttype:type,
        sortdir:uppresence})
        .done( function(data){
            $('#serverstatus').append('Done!' + '&#13;&#10;');
            data = JSON.parse(data);
            data[0] = JSON.parse(data[0]);
            data[1] = JSON.parse(data[1]);

            if (search == 'mp'){
                $("#mpresults > tbody").empty().append(data[0][0]);
                if (data[1][1] != ''){
                    $("#wokresults > tbody").empty().append(data[1][1]);
                }
            } else {
                $("#wokresults > tbody").empty().append(data[0][0]);
                if (data[0][1] != ''){
                    $("#mpresults > tbody").empty().append(data[0][1]);
                }
            }
            })
        .fail(function(xhr, textStatus, errorThrown){
            $('#serverstatus').append('&#13;&#10;' + '*****ERROR THROWN*****' + '&#13;&#10;');
            alert("error");
        });

    $('.mpresultTitle').each(function(){
        $(this).text($(this).text().replace('\u25b2','').replace('\u25bc',''))
    });

    if (uppresence) {
        $(elem).text($(elem).text() + '\u25bc')
    } else {
        $(elem).text($(elem).text() + '\u25b2')
    }
}


if(typeof(EventSource) !== "undefined") {
    var source = new EventSource("/update");
    source.onmessage = function(event) {
        $('#serverstatus').append(event.data + "&#13;&#10;")
    };
} else {
    $('#serverstatus').append("Your browser does not support server side live updates" + "&#13;&#10;")
}


$(document).ready(function() {
    $.get("/grabpresets", {set:'sulfides'}, function(data){
        sulfides=data.split("', '");
    });
    $.get("/grabpresets", {set:'selenides'}, function(data){
        selenides=data.split("', '");
    });
    $.get("/grabpresets", {set:'twoMetals'}, function(data){
        twoMetals=data.split("', '");
    });
    $.get("/grabpresets", {set:'oxides'}, function(data){
        oxides=data.split("', '");
    });
    $.get("/grabpresets", {set:'vanadates'}, function(data){
        vanadates=data.split("', '");
    });
    $.get("/grabpresets", {set:'keywords'}, function(data){
        keywords=data.split("', '");
    });

    $('#showmp').click(function(){
        if ($(this).text()=='Display MP Results'){
            $(this).text('Hide MP Results');
        } else {
            $(this).text('Display MP Results');
        };
        $('#mpresults').toggle(500)
    });

    $('.element').click(function(){
        var set = $("input[name=permset]:checked").val();

        switch(set) {
            case "A":
                if ($("#permtextA").val().includes($(this).text())){
                    var s = $("#permtextA").val();
                    s = s.replace($(this).text() + ', ','');
                    s = s.replace($(this).text());
                    $("#permtextA").val(s);
                    $(this).css('background', 'white');
                } else {
                    $(this).css('background', '#3366FF');
                    $("#permtextA").val($("#permtextA").val() + $(this).text() + ', ');
                }
                break;
            case "B":
                if ($("#permtextB").val().includes($(this).text())){
                    var s = $("#permtextB").val();
                    s = s.replace($(this).text() + ', ','');
                    s = s.replace($(this).text());
                    $("#permtextB").val(s);
                    $(this).css('background', 'white');
                } else {
                    $(this).css('background', '#FF5050');
                    $("#permtextB").val($("#permtextB").val() + $(this).text() + ', ');
                }
                break;
            case "C":
                if ($("#permtextC").val().includes($(this).text())){
                    var s = $("#permtextC").val();
                    s = s.replace($(this).text() + ', ','');
                    s = s.replace($(this).text());
                    $("#permtextC").val(s);
                    $(this).css('background', 'white');
                } else {
                    $(this).css('background', '#33CC33');
                    $("#permtextC").val($("#permtextC").val() + $(this).text() + ', ');
                }
                break;
            case "D":
                if ($("#permtextD").val().includes($(this).text())){
                    var s = $("#permtextD").val();
                    s = s.replace($(this).text() + ', ','');
                    s = s.replace($(this).text());
                    $("#permtextD").val(s);
                    $(this).css('background', 'white');
                } else {
                    $(this).css('background', '#FF00FF');
                    $("#permtextD").val($("#permtextD").val() + $(this).text() + ', ');
                }
                break;
        }

        sumPerm();
    });

    $('#permtextA, #permtextB, #permtextC, #permtextD').on('input', sumPerm());

    $("input[name=permset]").change(function(){
        var set = $("input[name=permset]:checked").val()

        var acolor = '#99CCFF', bcolor = '#FF9999', ccolor = '#99FF99', dcolor = '#FF99FF';

        switch(set) {
            case "A":
                acolor = '#3366FF';
                break;
            case "B":
                bcolor = '#FF5050';
                break;
            case "C":
                ccolor = '#33CC33';
                break;
            case "D":
                dcolor = '#FF00FF';
                break;
        }

        $(".element").each(function(){
            switch($(this).css('background-color')) {
                case "rgb(51, 102, 255)":
                case "rgb(153, 204, 255)":
                    $(this).css('background',acolor);
                    break;
                case "rgb(255, 80, 80)":
                case "rgb(255, 153, 153)":
                    $(this).css('background',bcolor);
                    break;
                case "rgb(51, 204, 51)":
                case "rgb(153, 255, 153)":
                    $(this).css('background',ccolor);
                    break;
                case "rgb(255, 0, 255)":
                case "rgb(255, 153, 255)":
                    $(this).css('background',dcolor);
                    break;
            }
        });
    });

    $('#addperm').click(function(){
        $('#queries').val($('#queries').val() + $('#permsum').val() + '; ');
        $("#permtextA").val('');
        $("#permtextB").val('');
        $("#permtextC").val('');
        $("#permtextD").val('');
        $("#permsum").val('');
        $(".element").each(function(){
            $(this).css('background', 'white');
        });
    });

    $('#showwok').click(function(){
        if ($(this).text()=='Display WoK Results'){
            $(this).text('Hide WoK Results');
        } else {
            $(this).text('Display WoK Results');
        };
        $('#wokresults').toggle(500)
    });

    $('#mpbutton, #wokbutton, #csvbutton, #loadbutton').click(function(event) {
        $('#serverstatus').empty().append('Generating results... Please wait...' + "&#13;&#10;");

        url = $('#ajaxform').attr( "action" );

        event.preventDefault();

        $.post(url,{
            queries:$('[name="queries"]').val(),
            keywords:$('[name="keywords"]').val(),
            name:$('[name="searchname"]').val(),
            searchlimit:$('[name="searchlimit"]').val(),
            load:$('#prevLoad option:selected').text(),
            searchtype:$(this).val()},

            function(data){
                $('#serverstatus').append('Done!' + '&#13;&#10;');
                data = JSON.parse(data);

                if (event.target.id == 'mpbutton'){

                    $('[name="queries"]').val(data[2])
                    $('[name="keywords"]').val(data[3])
                    $("#mptitle").empty().append(data[1])
                    $("#mpresults > tbody").empty().append(data[0]);
                    $("#prevLoad").append($('<option>', {value: data[1]}).text(data[1]));

                } else if (event.target.id == 'wokbutton') {

                    $('[name="queries"]').val(data[3])
                    $('[name="keywords"]').val(data[4])
                    $("#woktitle").empty().append(data[2])
                    $("#wokcols").empty().append(data[0]);
                    $("#wokresults > tbody").empty().append(data[1]);
                    $("#prevLoad").append($('<option>', {value: data[2]}).text(data[2]));

                } else if (event.target.id == 'csvbutton') {
                    $('#response').empty().append("Done! CSV-WC's generated. Check " + data[0]);

                } else if (event.target.id == 'loadbutton') {
                    var loadfile = $('#prevLoad option:selected').text()

                    $('[name="queries"]').val(data[2])
                    $('[name="keywords"]').val(data[3])
                    if (loadfile.substr(-7) == '_mp.txt'){
                        $("#mpresults > tbody").empty().append(data[0]);
                    } else if (loadfile.substr(-8) == '_wok.txt'){
                        $("#wokresults > thead > tr").empty().append(data[0]);
                        $("#wokresults > tbody").empty().append(data[1]);
                    }
                }
        })
        .fail(function(xhr, textStatus, errorThrown){
            $('#serverstatus').append('&#13;&#10;' + '*****ERROR THROWN*****' + '&#13;&#10;');
            alert("error");
        });
    });

});