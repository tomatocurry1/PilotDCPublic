$(document).ready(function() {
    function switch_reg_to_log() {
        $("#email").slideUp("fast");
        $("#map-wrapper").slideUp("fast");
        $("#latitude").slideUp("fast");
        $("#longitude").slideUp("fast");
        $("#login-to-register").addClass("hidden");
        $("#register-to-login").removeClass("hidden");
        $("#username").animate({"margin-top": "100px"}, "fast");
        $("#regbutton").text("Log in");
        $("#mainform").attr("action", "/login/");
    }

    function switch_log_to_reg() {
        $("#email").slideDown("fast");
        $("#map-wrapper").slideDown("fast");
        $("#latitude").slideDown("fast");
        $("#longitude").slideDown("fast");
        $("#login-to-register").removeClass("hidden");
        $("#register-to-login").addClass("hidden");
        $("#username").animate({"margin-top": "0px"}, "fast");
        $("#regbutton").text("Register");
        $("#mainform").attr("action", "/register/");
    }

    if (window.location.href.indexOf('?directlogin') > 0) {
        switch_reg_to_log();
    }

    $("#login-button").click(switch_reg_to_log);
    $("#register-button").click(switch_log_to_reg);
});