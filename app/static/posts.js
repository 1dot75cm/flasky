// 为相对时间添加 title 属性
$(document).ready(function() {
    $(".post-date span").each(function() {
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
