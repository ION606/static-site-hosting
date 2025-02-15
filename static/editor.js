function formatOption(option) {
	if (!option.id) {
		return option.text;
	}
	const $option = $(`
	  <div class="custom-option">
		<span class="option-text">${option.text}</span>
	  </div>
	`);
	return $option;
}


document.addEventListener("DOMContentLoaded", () => {
	const storedTheme = localStorage.getItem('editortheme');

	// for each textarea (one per file) replace with Ace Editor
	const editors = Array.from(document.querySelectorAll('textarea')).map((textarea) => {
		const language = textarea.dataset.language,
			themeStyle = document.querySelector('#theme-style'),
			isDark = themeStyle.href.includes('dark-styles.css'),
			aceTheme = isDark ? "ace/theme/twilight" : "ace/theme/chrome",
			editorContainer = document.createElement('div');

		editorContainer.style.width = "100%";
		editorContainer.style.height = "400px";

		// insert the container after the textarea
		textarea.parentNode.insertBefore(editorContainer, textarea.nextSibling);
		// hide the original textarea
		textarea.style.display = "none";

		const editor = ace.edit(editorContainer);
		editor.setTheme(storedTheme || aceTheme);

		let aceMode = "ace/mode/html"; // default fallback
		if (language === "css") {
			aceMode = "ace/mode/css";
		} else if (language === "javascript") {
			aceMode = "ace/mode/javascript";
		} else if (language === "htmlmixed") {
			aceMode = "ace/mode/html";
		}
		editor.session.setMode(aceMode);

		// set initial content from the textarea and add options
		editor.session.setValue(textarea.value.trim());
		editor.setOptions({
			fontSize: "14px",
			tabSize: 4,
			useSoftTabs: true,
			wrap: true,
			showPrintMargin: false
		});

		// update the hidden textarea whenever the Ace content changes
		editor.session.on('change', () => {
			textarea.value = editor.getValue();
		});

		return editor;
	});

	// Retrieve the list of available themes
	const ThemeList = ace.require("ace/ext/themelist"),
		themes = ThemeList.themes,
		themeSelector = document.querySelector('#theme-selector');

	themes.forEach(function (theme) {
		var option = document.createElement('option');
		option.value = theme.theme;
		option.textContent = theme.caption;
		themeSelector.appendChild(option);
	});

	if (storedTheme) themeSelector.value = storedTheme;

	// Initialize Select2 on the theme selector
	$(themeSelector).select2({
		templateResult: formatOption,
		placeholder: 'Select a theme',
		allowClear: true
	}).on('change', function (_) {
		localStorage.setItem('editortheme', themeSelector.value)
		editors.forEach(editor => editor.setTheme(themeSelector.value));
	});
});