// 为相对时间添加 title 属性
$(document).ready(function() {
    $(".post-date, .comment-date span").each(function() {
        var ts = $(this).attr('data-timestamp');
        var t = moment(ts).format('LLL');
        $(this).attr('title', t);
    });
});

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
$(function() {
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
});
