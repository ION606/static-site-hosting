document.addEventListener('DOMContentLoaded', function () {
	const button = document.querySelector('#click-me');
	if (button) {
		button.addEventListener('click', function () {
			alert('Button clicked!');
		});
	}
});