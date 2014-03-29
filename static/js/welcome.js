$(document).ready(function() {
	$("body").hide().fadeIn("slow");
	
	$("#login-button").click(function() {
		$("#email").slideUp("fast");
		$("#latitude").slideUp("fast");
		$("#longitude").slideUp("fast");
		$("#login-to-register").addClass("hidden");
		$("#register-to-login").removeClass("hidden");
		$("#username").animate({"margin-top": "100px"}, "fast");
		$("#regbutton").text("Log in");

	});

	$("#register-button").click(function() {
		$("#email").slideDown("fast");
		$("#latitude").slideDown("fast");
		$("#longitude").slideDown("fast");
		$("#login-to-register").removeClass("hidden");
		$("#register-to-login").addClass("hidden");
		$("#username").animate({"margin-top": "60px"}, "fast");
		$("#regbutton").text("Register");

	})
});