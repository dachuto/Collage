"use strict";
function load_script(url) {
	var head= document.getElementsByTagName('head')[0];
	var script= document.createElement('script');
	script.type= 'text/javascript';
	script.src= url;
	head.appendChild(script);
}

load_script('https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js');
load_script('https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.3.1/semantic.min.js');