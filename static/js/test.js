$(document).ready(function() {
	$("#brand").bind("load", function() {
		$("h1").hide().fadeIn("slow");
		$(this).hide().fadeIn("slow");
	});
});