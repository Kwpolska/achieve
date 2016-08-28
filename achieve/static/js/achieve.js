if (typeof tageditor !== 'undefined') {
    $("#tageditor_btn").click(function() {
        $("#tageditor_btn").hide();
        $("#tageditor").show();
        return false;
    });
}

// Filters are hidden on mobile by default
$(".filter-show-btn").click(function() {
    $(".filter-line").toggle();
});

var reminderTimeout = -1;
var timeoutIds = [];

function makeNotification(task) {
    return function() {
        n = new Notification(task.title, {
            "body": task.description,
            "icon": "/static/img/achieve128.png",
            "tag": "notification_" + task.id
        });
        n.onclick = function() {
            event.preventDefault();
            window.open(task.url + "?reminder_seen=True", '_blank');
        };
    }
}

function setReminders() {
    if (localStorage.getItem('showReminders') != '1') return;
    $.getJSON("/api/reminders/soon/").done(function(data) {
        now = Date.now();
        for (var i = 0; i < timeoutIds.length; i++) {
            clearTimeout(timeoutIds);
        }
        for (var i = 0; i < data.reminders.length; i++) {
            timeoutLength = (data.reminders[i].timestamp * 1000) - now;
            if (timeoutLength < 1000) {
                timeoutLength = 1000;
            }
            tid = setTimeout(makeNotification(data.reminders[i]), timeoutLength);
            timeoutIds.push(tid);
        }
        //
        // check back tomorrow
        reminderTimeout = setTimeout(setReminders, 86400000);
    }).fail(function(data) {
        console.log("Failed to update reminders: " + data);
        // check back in 5 minutes
        reminderTimeout = setTimeout(setReminders, 300000);
    });
}

function updatePopover(title, content) {
    $("#reminder-toggle").attr("data-original-title", title);
    $("#reminder-toggle").data("bs.popover").options.title = title;
    $("#reminder-toggle").data("bs.popover").options.content = content;
    $("#reminder-toggle").popover("hide");
}

function setReminderStatus(rStatus) {
    switch (rStatus) {
    case "nopermissions":
        faicon = 'fa-bell-o';
        tooltip = "Reminders missing permissions";
        text = "Reminders";
        updatePopover(tooltip, "You have not allowed notifications in your browser yet. Enable them to use reminders.");
        break;
    case "enabled":
        faicon = 'fa-bell';
        tooltip = "Disable reminders";
        text = tooltip;
        updatePopover(tooltip, "Reminders are enabled. Click on the icon to disable.");
        break;
    case "disabled":
        faicon = 'fa-bell-slash';
        tooltip = "Enable reminders";
        text = tooltip;
        updatePopover(tooltip, "Reminders are supported but disabled. Click on the icon to enable.");
        break;
    case "blocked":
        faicon = 'fa-bell-o-slash';
        tooltip = "Reminders blocked";
        text = tooltip;
        updatePopover(tooltip, "You denied permission to show you notifications. Change your browser’s settings to use reminders.");
        break;
    case "unsupported":
        faicon = 'fa-bell-o-slash';
        tooltip = "Reminders unsupported";
        text = tooltip;
        updatePopover(tooltip, "Your browser does not support notifications, please upgrade to use reminders.");
    }
    $("#reminder-icon").attr('class', 'fa fa-fw ' + faicon);
    $("#reminder-toggle").attr('title', tooltip);
    $("#reminder-text").text(text);
}

function enableReminders() {
    localStorage.setItem('showReminders', '1');
    setReminderStatus("enabled");
    setReminders();
}

function disableReminders() {
    setReminderStatus("disabled");
    localStorage.setItem('showReminders', '0');
    if (reminderTimeout !== -1) {
        clearTimeout(reminderTimeout);
        reminderTimeout = -1;
    }
}

function toggleReminders() {
    if ("Notification" in window && Notification.permission === "granted") {
        current = localStorage.getItem('showReminders');
        if (current === undefined || current === '0') {
            enableReminders();
            setReminders();
        } else if (current === '1') {
            disableReminders();
        }
    }
}

$(document).ready(function() {
    // jQuery UI date pickers
    $(".datepicker").datepicker({
      showButtonPanel: true,
      dateFormat: "yy-mm-dd"
    });

    // Date copying
    $(".copy-datetime").click(function() {
        o = $(this);
        from0 = '#' + o.attr('data-from');
        from1 = from0.slice(0, -1) + '1';
        to0 = '#' + o.attr('data-to');
        to1 = to0.slice(0, -1) + '1';
        $(to0).val($(from0).val());
        $(to1).val($(from1).val());
    });

    // Collection Mode Ctrl+Enter
    $("#collection-box").keydown(function(event) {
        if ((event.keyCode == 10 || event.keyCode == 13) && event.ctrlKey) {
            this.parentElement.parentElement.submit();
        }
    });

    // Reminder support
    $("#reminder-toggle").popover({"title": "Reminders", "content": ""});
    if (!("Notification" in window)) {
        setReminderStatus("unsupported");
    }
    else if (Notification.permission === "granted") {
        enableReminders();
    }
    else if (Notification.permission !== 'denied') {
        setReminderStatus("nopermissions");
        Notification.requestPermission(function (permission) {
            if (permission === "granted") {
                enableReminders();
            } else {
                disableReminders();
            }
        });
    } else {
        disableReminders();
        console.log("User denied notifications");
    }
    $("#reminder-toggle").click(function() {
        toggleReminders();
        return false;
    });
});
