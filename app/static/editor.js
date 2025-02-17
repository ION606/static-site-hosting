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


function getAceMode(language) {
	let aceMode = "ace/mode/html"; // default fallback
	if (language === "css") {
		aceMode = "ace/mode/css";
	} else if (language === "javascript") {
		aceMode = "ace/mode/javascript";
	} else if (language === "htmlmixed") {
		aceMode = "ace/mode/html";
	}
	return aceMode;
}

document.addEventListener("DOMContentLoaded", () => {
	const storedTheme = localStorage.getItem('editortheme');

	// Initialize Ace editor instance on the container
	const editor = ace.edit("editor-container");
	editor.setTheme("ace/theme/chrome");

	// Default mode as html mixed. It will be updated based on file type.
	editor.session.setMode("ace/mode/html");

	// To track the current file (index)
	var currentFileIndex = null;

	// Returns Ace mode based on file extension
	function getAceMode(filename) {
		if (filename.endsWith('.css')) return "ace/mode/css";
		if (filename.endsWith('.js')) return "ace/mode/javascript";
		return "ace/mode/html";
	}

	// When a file card is clicked then load its content into the editor
	document.querySelectorAll('#file-list .file-card').forEach((card) => {
		card.addEventListener('click', () => {
			// Save changes of currently open file
			if (currentFileIndex !== null) document.getElementById(`textarea-${currentFileIndex}`).value = editor.getValue();
			currentFileIndex = card.getAttribute("data-index");

			// Get filename and load content from corresponding hidden textarea
			const filename = card.getAttribute("data-file");
			editor.setValue(document.getElementById(`textarea-${currentFileIndex}`).value);
			editor.session.setMode(getAceMode(filename));

			// Show the editor container
			document.getElementById("editor-container").classList.add("visible");
		});
	});

	// Update the corresponding hidden textarea whenever the editor value changes
	editor.session.on("change", function (e) {
		if (currentFileIndex !== null) {
			const ta = document.getElementById("textarea-" + currentFileIndex);
			ta.value = editor.getValue();
		}
	});

	// Initialize Select2 for the theme selector
	$(document).ready(function () {
		$('#theme-selector').select2({
			templateResult: formatOption,
			placeholder: 'Select a theme',
			allowClear: true
		}).on('change', function () {
			const selectedTheme = $('#theme-selector').val();
			localStorage.setItem('editortheme', selectedTheme);
			editor.setTheme(selectedTheme);
		});
	});

	// Retrieve the list of available themes
	const ThemeList = ace.require("ace/ext/themelist"),
		themes = ThemeList.themes,
		themeSelector = document.querySelector('#theme-selector');

	themes.forEach((theme) => {
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
		const selectedTheme = $('#theme-selector').val();
		localStorage.setItem('editortheme', selectedTheme);
		editor.setTheme(selectedTheme);
	});

	// Add event listener for Ctrl+S to save the current file
	//TODO: save this
	const editEl = document.querySelector('#editor-container');

	document.addEventListener('keydown', (e) => {
		if (e.ctrlKey && e.key === 's') {
			e.preventDefault();
			if (currentFileIndex !== null) {
				document.getElementById("textarea-" + currentFileIndex).value = editor.getValue();
				document.querySelector("form").submit();
			}
		}
		else if (editEl.contains(e.target)) {
			document.getElementById("textarea-" + currentFileIndex).value = editor.getValue();
		}
	});

	// form submit intercept
	document.querySelector("form").addEventListener("submit", async (e) => {
		e.preventDefault();

		const formData = new FormData();
		document.querySelectorAll("[id^='textarea-']").forEach((textarea) => {
			if (textarea.dataset.edited === "true") {
				formData.append(textarea.name, textarea.value);
				delete textarea.dataset.edited;
			}
		});

		await fetch(window.location.href, {
			method: "POST",
			headers: {
				"X-Requested-With": "XMLHttpRequest"
			},
			body: formData
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.success) {
					alert("Site updated successfully!"); // Or display a flash message
				}
			})
			.catch((error) => {
				console.error("Error:", error);
			});
	});
});
