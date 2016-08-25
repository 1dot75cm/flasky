// 为相对时间添加 title 属性
$(document).ready(function() {
    $(".post-date span").each(function() {
        var ts = $(this).attr('data-timestamp');
        var t = moment(ts).format('LLL');
        $(this).attr('title', t);
    });
});
