// THIS CODE IS TERRIBLE

$(document).ready(function() {
    google.maps.event.addDomListener(window, 'load', initialize);
    $("#useaddress").click(code_address);

    $("#address").val("20815");
});

var geocoder;
var map;
var marker;

function set_lat_long(coords) {
    $("#longitude").val(coords.k);
    $("#latitude").val(coords.A);
}

function initialize() {
    geocoder = new google.maps.Geocoder();
    var latlng = new google.maps.LatLng(-77.0737, 38.9875);
    var mapOptions = {
        zoom: 8,
        center: latlng
    };
    map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
}

function code_address() {
    var address = document.getElementById('address').value;
    geocoder.geocode( { 'address': address}, function(results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
            map.setCenter(results[0].geometry.location);
            if (marker) {
                marker.setMap(null);
            }
            marker = new google.maps.Marker({
                map: map,
                position: results[0].geometry.location,
                draggable: true
            });
            set_lat_long(marker.getPosition());
            google.maps.event.addListener(marker, 'dragend', function() {
               set_lat_long(marker.getPosition());
            });
        } else {
            console.log('Geocode was not successful for the following reason: ' + status);
        }
    });
}