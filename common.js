"use strict";
function load_script(url) {
	const promise = new Promise((resolve, reject) => {
		const head = document.getElementsByTagName('head')[0];
		const script = document.createElement('script');
		head.appendChild(script);
		script.type = 'text/javascript';
		script.onload = resolve;
		script.src = url;
	});
	return promise;
}

load_script('https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js');
load_script('https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.js');