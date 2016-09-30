// 为相对时间添加 title 属性
var timeTitle = function() {
    $(".post-date span, .comment-date span, .table-date span").each(function() {
        var ts = $(this).attr('data-timestamp');
        var t = moment(ts).format('LLL');
        $(this).attr('title', t);
    });
}

// textarea 文本域自适应高度
$.fn.autoHeight = function() {
    function autoHeight(elem) {
        elem.style.height = 'auto';
        elem.scrollTop = 0; // 防抖动
        elem.style.height = elem.scrollHeight + 'px';
    }
    this.each(function() {
        autoHeight(this);
        $(this).on('keyup', function() {
            autoHeight(this);
        });
    });
}

$('textarea[id=flask-pagedown-body]').attr('autoHeight', 'True');
$('textarea[autoHeight]').autoHeight();

// 移动端减小导航条长度
var mobileBar = function() {
    if ($(window).width() <= 720) {  // 可见区域宽
        var curr = Number($('.pagination li.active a').text());
        var last = $('.pagination li:last').prev().children().text(); // 倒数第二个
        var list = ['1', String(curr-1), String(curr), String(curr+1), last];
        if (curr == 1) {
            list.push('3', '4', '5');
        } else if (curr == 2) {
            list.push('4', '5');
        } else if (curr == 3) {
            list.push('5');
        } else if (curr == 4 || curr == 5) {
            list.push('2');
        }
        $('.pagination li').each(function () {
            var n = $(this).children().text();
            if ($.inArray(n, list) != - 1 ||
                String(Number(n)) == 'NaN') {
                return true;  // 相当于continue
            } else {
                $(this).remove();
            }
        });
        $('.page-header img').css('height', '40px');  // 调整用户页图片大小
        $('.profile-header').css('margin-left', '50px');
    }
}


/* 目录导航 */
var sideBar = function () {
    var content = '<ul>',
        tags = $('.post-body h1, .post-body h2, .post-body h3');

    for (let i=0, j=0; i<$(tags).length; i++) {
        if (tags[i].tagName === 'H1') {
            content = $(content).append('<li><a>' +$(tags[i]).text()+ '</a></li>');
        }
        if (tags[i].tagName === 'H2' && tags[i-1].tagName === 'H1') {
            var top_li = $(content).find('li').eq(i-1).append('<ul><li><a>' +$(tags[i]).text()+ '</a></li></ul>');
            j++;
        }
        if (tags[i].tagName === 'H2' && tags[i-1].tagName === 'H2') {
            $(content).find('li ul').eq(j-1).append('<li><a>' +$(tags[i]).text()+ '</a></li>');
        }
        if (tags[i].tagName === 'H2' && tags[i-1].tagName === 'H3') {
            top_li.children('ul').append('<li><a>' +$(tags[i]).text()+ '</a></li>');
        }
        if (tags[i].tagName === 'H3' && tags[i-1].tagName === 'H2') {
            $(content).find('li').eq(i-1).append('<ul><li><a>' +$(tags[i]).text()+ '</a></li></ul>');
            j++;
        }
        if (tags[i].tagName === 'H3' && tags[i-1].tagName === 'H3') {
            $(content).find('li ul').eq(j-1).append('<li><a>' +$(tags[i]).text()+ '</a></li>');
        }
    }
    for (let i=0; i < $(tags).length; i++) {
        $(tags[i]).attr('id', 'title'+i);
    }

    var barContent = $('<div>').append(content);
    barContent.attr('id', 'sideBarContents');
    barContent.css('display', 'none');
    var barTitle = $('<div>').append('<h2>TitleBar</h2>');
    barTitle.attr('id', 'sideBarTab');
    var bar = $('<div>').append(barTitle, barContent);
    bar.attr('id', 'sideBar');
    $('.post-body').append(bar);

    var item = $('#sideBar a');
    for (let i=0; i < $(item).length; i++) {
        $(item[i]).attr('href', '#title'+i);
    }
}

/* QR Code Image */
var QRCode = function(event) {
    event.stopPropagation();  // 取消事件冒泡, 不向父辈元素传递事件
    let n = $(".qrcode-sm").index(this);  // 当前元素序号
    let width = ($(window).width() - $(".qrcode").first().width()) / 2;
    let height = ($(window).height() - $(".qrcode").first().height()) / 2;
    $(".qrcode:not(:eq("+n+")):visible").hide();  // 隐藏除当前元素外的可见元素
    $(".qrcode").eq(n).css({right: width, top: height}).toggle(200);
}
$(".qrcode-sm").on("click", QRCode);  // 移动端绑定 touchend 事件
$(".qrcode").click(function() { $(this).fadeOut(500); });  // 淡出
$(document).click(function() { $(".qrcode").slideUp(); }); // 滑动


$(function() {
    timeTitle();
    mobileBar();
    sideBar();
    $("#sideBar").mouseenter(function() {
        $("#sideBarContents").css("display", "block");
    });
    $("#sideBar").mouseleave(function() {
        $("#sideBarContents").css("display", "none");
    });
    /* 图片父元素添加居中 */
    $(".post-body img, .flask-pagedown-preview img").parent("p")
        .css("text-align", "center");
    $(".flask-pagedown-preview").mouseenter(function() {
        $(".flask-pagedown-preview img").parent("p")
            .css("text-align", "center");
    });
    /* 图片添加链接 */
    $(".post-body img").each(function() {
        let img = $(this).clone(true);
        $("<a>").attr("href", img.attr("src"))
            .attr("title", img.attr("alt"))
            .append(img).replaceAll($(this));
    });
});
