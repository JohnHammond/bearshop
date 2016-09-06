$(document).ready(function(){

	$('.flashed_messages').delay(2000).fadeOut(1000);


	$(":file").change(function () {
	    if (this.files && this.files[0]) {
	        var reader = new FileReader();
	        reader.onload = picture_uploaded;
	        reader.readAsDataURL(this.files[0]);
	    }
	});


	$('img').load(function(){
		if ($(this).attr('src') != "" ){
			// alert('image exists');
			$(this).attr('width', '325px');
			$(this).attr('height', '325px');
		}
	});
});

function picture_uploaded(e){

	picture = e.target.result;
	$('img').attr('src', picture);
	$('img').attr('width', 250);
	$('img').attr('height', 250);
	$('img').css('display', 'block');
	// Center the image now that it has been uploaded
}