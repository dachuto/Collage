"use strict";

class cards_data_source {
	id_to_name(multiverse_id) {
		return "TODO";
	}

	scryfall_link(name) {
		const url = "https://scryfall.com/search?q=%21%22" + name + "%22";
		return '<a href="' + url + '">' + name + '</a>';
	}

	id_to_html(multiverse_id) {
		return this.scryfall_link(this.id_to_name(multiverse_id))
	}

	image_url(multiverse_id) {
		// return "https://api.scryfall.com/cards/multiverse/" + multiverse_id + "?format=image";
		return "http://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid=" + multiverse_id;
	}
}

function convert_article(article, source) {
	let re = /#([a-z]+)\((.*?)\)/g;

	let tags = new Array();
	function replacer(match, p0, p1, offset, string) {
		tags.push(Number(p1));
		return source.id_to_html(p1);
	}

	return [$.parseHTML(article.replace(re, replacer)), tags];
}

function error_message_html(header, inside) {
	let icon = $("<i/>", {
		class: "exclamation triangle icon"
	});
	let content = $("<div/>", {
		class: "content",
	}).append($("<div/>", {
		class: "header",
		text: header
	})).append($("<p/>", {
		text: inside
	}));
	return $("<div>", {
		class: "ui red icon message",
	}).append(icon).append(content);
}

function JSON_request(file_name) {
	let request = $.getJSON(file_name).done(function (data, textStatus, jqXHR) {
	}).fail(function (jqXHR, textStatus, errorThrown) {
		DOM_append(error_message_html(file_name, errorThrown));
	});
	return request;
}

function DFS(graph, start, visit_pre, visit_post) {
	let encountered = new Set();
	let processed = new Set();
	let stack = [];

	let encounter = v => {
		if (!encountered.has(v)) {
			encountered.add(v);
			visit_pre(v);
			if (!processed.has(v)) {
				stack.push(v);
			}
		}
	};

	if (start !== undefined) {
		encounter(start);
	}

	for (const [i, unused] of graph) {
		encounter(i);

		while (stack.length != 0) {
			const vertex = stack[stack.length - 1];
			if (processed.has(vertex)) {
				stack.pop();
				visit_post(vertex);
				continue;
			}
			processed.add(vertex);
			let edges = graph.get(vertex);
			for (const destination of edges) {
				encounter(destination);
			}
		}
	}
}

function topological_order(graph) {
	let post_order = [];
	DFS(graph, undefined, ()=>{}, (v) => {
		post_order.push(v);
	});
	return post_order.reverse();
}

class tag {
	constructor(element, name) {
		this.element = element;
		this.name = name;
		this.state = "unset";
		this.state_implicit = null;
		this.timestamp = 0;
		this.timestamp_implicit = 0;
	}

	explicit() {
		switch (this.state) {
		case "in":
		case "out":
			return true;
		}
		return false;
	}

	max_timestamp() {
		return Math.max(this.timestamp, this.timestamp_implicit);
	}

	reset_implicit() {
		if (this.state_implicit !== null) {
			console.log("HAUDHSAD " + this.state_implicit);
		}
		this.state_implicit = null;
		this.timestamp_implicit = 0;
	}

	imply(destination) {
		if (destination.explicit()) {
			return;
		}

		if (destination.max_timestamp() > this.max_timestamp()) {
			return;
		}

		if (this.state == "unset" && this.state_implicit === null) {
			return;
		}

		if (this.state == "in" || this.state_implicit == "in") {
			destination.state_implicit = "in";
			destination.timestamp_implicit = this.max_timestamp();
		}

		if (this.state == "out" || this.state_implicit == "out") {
			destination.state_implicit = "out";
			destination.timestamp_implicit = this.max_timestamp();
		}
	}

	rotate(current_timestamp) {
		const next_state = state => {
			switch (state) {
			case "unset":
				return "in";
			case "in":
				return "out";
			case "out":
				return "unset";
			}
		};
		this.state = next_state(this.state);
		if (this.explicit()) {
			this.timestamp = current_timestamp;
		} else {
			this.timestamp = 0;
		}
		this.update_element();
	}

	css_class() {
		if (this.state_implicit === null) {
			return "card_tag_" + this.state;
		} else {
			return "card_tag_" + this.state_implicit + "_implicit";
		}
	}

	update_element() {
		const inner = this.element.firstChild;
		inner.className ="";
		inner.classList.add("card_tag_inner", this.css_class());
	}
}

class page_data {
	constructor() {
		this.backend_url = new URL("http://localhost:8080");
		this.images_info = {loaded: 0, total: 0};
		this.message_box = document.querySelector("#message_box");
		this.message_box_timer = null;
		this.source = new cards_data_source();
		this.search_button = document.getElementById("search_button");
		this.search_input = document.getElementById("search_input");
		this.search_input.value = window.location.search;
		this.search_button.onclick = () => {
			// console.log(encodeURIComponent(SI.value));
			// data.start_async_loading();
			// window.history.pushState(null, "", "http://localhost:1234/mtg_results.html?set=BBD");
			// window.history.replaceState(null, "", "http://localhost:1234/mtg_results.html?set=BBD");
		};
	}

	start_async_loading() {
		console.log(location);
		console.log(decodeURIComponent(location.search));

		let info_url = new URL("/info", this.backend_url);
		let query_url = new URL("/query", this.backend_url);
		query_url.search = window.location.search;

		$.when(
			JSON_request(info_url.href),
			JSON_request(query_url.href)
		).then(
			this.async_complete.bind(this),
			null
		);
	}

	request_card_names_to_ids(card_names_list) {
		let requests = [];
		for (const name of card_names_list) {
			let url = new URL("/query", this.backend_url);
			url.search = "name=" + name;
			let attach_name_and_always_succeed = $.getJSON(url.href).then(
				value => ({name:name, value:value}),
				error => ({name:name, error:error})
			);
			requests.push(attach_name_and_always_succeed);
		}

		return Promise.all(requests).then(results => {
			return results.reduce((accumulator, element) => {
				if (element.hasOwnProperty('value')) {
					accumulator[0].push([element.name, element.value]);
				} else if (element.hasOwnProperty('error')) {
					accumulator[1].push([element.name, element.error]);
				} else {
					console.assert(false, "missing property");
				}
				return accumulator;
			}, [[], []]);
		});
	}

	async_complete_2(card_name_to_ids_list) {
		// let id_list = [];
		// for (const e of card_name_to_ids_list) {
		// 	const [name, card_ids] = e;

		// 	id_list = [ ...id_list, ...card_ids];
		// }
	}

	start_async_loading_2(card_names_list) {
		this.request_card_names_to_ids(card_names_list).then(value => {
			let [success, error] = value;
			console.log(success);
			console.log(error);
			// this.async_complete_2(success);

			DOM_append(images_grid(success, this.source));
			//TODO: RESTORE!
			this.start_lazy_images_loading();
		});
	}

	async_complete(info, query) {
		this.graph = new Map();
		this.tags = new Map();
		this.tags_timestamp = 0;
		for (const [key, value] of Object.entries(info[0])) {
			const tag_id = Number(key);
			const element = this.card_tag_html(tag_id, value);
			$("#card_tags_container").append(element);
			this.graph.set(tag_id, []);
			const t = new tag(element, name);
			this.tags.set(tag_id, t);
			t.update_element();
		}
		//TODO: this graph comes from info server !!! >>
		this.graph.set(1, [2]);
		this.graph.set(100, [102, 104]);
		this.graph.set(102, [103, 104]);
		// << ----------------------------
		console.log(this.graph);
		this.graph_topological_order = topological_order(this.graph);

		this.append_images_grid(query[0]);
	}

	card_tag_html(id, name, state) {
		let inner = document.createElement("div");
		inner.classList.add(state);
		inner.setAttribute("data-id", id);
		inner.innerHTML = name;

		let tag = document.createElement("div");
		tag.className = "card_tag_item";
		tag.onclick = event => {
			// console.log(event);
			++this.tags_timestamp;
			this.tags.get(id).rotate(this.tags_timestamp);

			for (const [id, t] of this.tags) {
				t.reset_implicit();
			}

			for (const x of this.graph_topological_order) {
				const source = this.tags.get(x);
				for (const destination_id of this.graph.get(x)) {
					const destination = this.tags.get(destination_id);
					source.imply(destination);
				}
			}

			for (const [id, t] of this.tags) {
				t.update_element();
			}
		};
		tag.appendChild(inner);
		return tag;
	}

	start_lazy_images_loading() {
		let options = {
			root: null,
			rootMargin: '150%',
			threshold: [0.0]
		};

		let observer = new IntersectionObserver((entries, observer) => {
			for (const e of entries) {
				if (e.isIntersecting) {
					image_load(e.target);
					++this.images_info.loaded;
					this.update_message_box();
					observer.unobserve(e.target);
				}
			}
		}, options);

		for (const t of document.querySelectorAll(".image-inactive")) {
			++this.images_info.total;
			observer.observe(t);
		}
	}

	update_message_box() {
		$(this.message_box)
			.addClass("opaque")
			.text("Images " + this.images_info.loaded + "/" + this.images_info.total);
		if (this.message_box_timer != null) {
			window.clearTimeout(this.message_box_timer);
		}
		this.message_box_timer = window.setTimeout(() => {
			this.message_box.classList.remove("opaque");
		}, 5000);
	}
}

function DOM_ready() {
	$.when(
		JSON_request("mtg/article.json"),
		JSON_request("mtg/name_to_tag.json"),
		JSON_request("mtg/tags.json")
	).then(all_data_is_here, null);
}

function DOM_ready_wants() {
	// $.when(
	// 	JSON_request("mtg/wants.json"),
	// ).then(all_data_is_here_wants, null);

	$.when(
		JSON_request("mtg/articles/commander_teysa.json"),
	).then(all_data_is_here_deck, null);
}

function select_element_by_id(id) {
	return () => {
		let selection = window.getSelection();
		let range = document.createRange();
		range.selectNodeContents(document.getElementById(id));
		selection.removeAllRanges();
		selection.addRange(range);
	};
}

function as_deck(list) {
	let sorted = Array.from(list).sort();
	let text = "";
	for (const name of list) {
		text += "1 " + name + "\n";
	}
	return text;
}

function as_pretty_json(list) {
	let sorted = Array.from(list).sort();
	let text = "";
	text += "[";
	let divider = false;
	for (const name of sorted) {
		if (divider) {
			text += ",";
		} else {
			divider = true;
		}
		text += "\n\"" + name + "\"";
	}
	text += "\n]";
	return text;
}

function all_data_is_here_wants(wants) {
	console.log(wants);
	
	//TODO: work with deck lists based on this!

	document.getElementById("deck_text").textContent = as_deck(wants);
	document.getElementById("deck_select_button").onclick = select_element_by_id("deck_text");
	document.getElementById("json_text").textContent = as_pretty_json(wants);
	document.getElementById("json_select_button").onclick = select_element_by_id("json_text");

	let data = new page_data();
	data.start_async_loading_2(wants);
}

function all_data_is_here_deck(deck) {
	// document.getElementById("deck_text").textContent = as_deck(wants);
	// document.getElementById("deck_select_button").onclick = select_element_by_id("deck_text");
	// document.getElementById("json_text").textContent = as_pretty_json(wants);
	// document.getElementById("json_select_button").onclick = select_element_by_id("json_text");

	let data = new page_data();
	data.start_async_loading_2(deck.main);
}

function DOM_ready_results() {
	document.addEventListener("keyup", event => { //TODO: handle keys to do simple searches
		console.log(event);
		// if (event.key !== "Enter") return; // Use `.key` instead.
		// document.querySelector("#linkadd").click(); // Things you want to do.
		event.preventDefault(); // No need to `return false;`.
	});
	let data = new page_data();
	data.start_async_loading();
}

function DOM_append(element) {
	$("#main_content").append(element);
}

function set_to_string(set) {
	return JSON.stringify(Array.from(set));
}

class group_by_keys_set {
	static add(map, html, keys) {
		let keys_set = new Set(keys);
		let as_string = set_to_string(keys_set);

		if (map.has(as_string)) {
			const e = map.get(as_string);
			e.content.push(html);
		} else {
			map.set(as_string, { keys: keys, content: [html] });
		}
	}

	static get(map) {
		let without_strings = new Map();
		for (const [k, v] of map) {
			without_strings.set(v.keys, v.content);
		}
		return without_strings;
	}
}

function articlesJSON_groupped(data, source) {
	let temp = new Map();

	for (let i in data) {
		let [html, keys] = convert_article(data[i], source);
		group_by_keys_set.add(temp, html, keys);
	}
	return group_by_keys_set.get(temp);
}

function list_svg() {
	let svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
	svg.setAttribute("viewBox", "0 0 24 24");
	let path_0 = document.createElementNS(svg.namespaceURI, "path");
	let path_1 = document.createElementNS(svg.namespaceURI, "path");
	path_0.setAttribute("d", "M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z");
	path_1.setAttribute("d", "M0 0h24v24H0z");
	path_1.setAttribute("fill", "none");
	svg.appendChild(path_0);
	svg.appendChild(path_1);
	return svg;
}

function list_overlay(hover_node, hidden_node) {
	const TRANSPARENT_STYLES = ["transparent-fully", "transparent-barely-visible", "transparent-almost-opaque"];
	let list_overlay = list_svg();
	list_overlay.classList.add("card-overlay");
	list_overlay.classList.add("list-overlay-position");
	list_overlay.classList.add("opacity-transition");
	list_overlay.classList.add(TRANSPARENT_STYLES[0]);
	
	$(hover_node).hover(function() {
		list_overlay.classList.add(TRANSPARENT_STYLES[1]);
	}, function() {
		list_overlay.classList.remove(TRANSPARENT_STYLES[1]);
	});

	$(list_overlay).hover(function() {
		list_overlay.classList.add(TRANSPARENT_STYLES[2]);
		hidden_node.classList.remove("invisible");
	}, function() {
		list_overlay.classList.remove(TRANSPARENT_STYLES[2]);
		hidden_node.classList.add("invisible");
	});

	return list_overlay;
}

function image_not_loaded_html(url) {
	let i = document.createElement("div");
	i.classList.add("aspect-ratio-box-inside", "image-inactive");
	i.setAttribute("data-src", url);
	return i;
}

function image_load(e) {
	let image = document.createElement("img");
	image.classList.add("aspect-ratio-box-inside", "preview");
	image.src = e.getAttribute("data-src");

	const parent = e.parentNode;
	parent.replaceChild(image, e);
}

function images_grid(name_to_id_list, source) {
	let images_grid = $("<div/>", {
		class: "images_grid",
	});

	for (const [name, ids] of name_to_id_list) {
		const chosen_index = ids.length - 1; //TODO: we take last (newest printing), maybe customize
		let hidden_printings = null;

		const hide_some_printings = (ids.length > 1);
		if (hide_some_printings) {
			hidden_printings = document.createElement("div");
			hidden_printings.classList.add("fullscreen", "images_grid", "invisible");
			document.getElementById("hidden_cards").appendChild(hidden_printings);
		}

		for (let k = 0; k < ids.length; ++k) {
			const id = ids[k];
			
			let d = document.createElement("div");
			d.classList.add("aspect-ratio-box");
			
			let i = image_not_loaded_html(source.image_url(id));
			d.appendChild(i);
			
			if (k == chosen_index) {
				if (hide_some_printings) {
					let hidden_name = document.createElement("div");
					hidden_name.textContent = name;
					hidden_name.classList.add("card-name-hidden");
					d.appendChild(hidden_name);
					
					d.appendChild(list_overlay(d, hidden_printings));
				}

				images_grid.append(d);
			} else {
				hidden_printings.appendChild(d);
			}
		}
	}
	return images_grid;
}

function item_html(keys, htmls, item_number, source) {
	let item = $("<div/>", {
		class: "article_grid"
	});

	let images_column = $("<div/>", {
		class: "images_column"
	});

	let sticker = $("<div/>", {
		class: "top_sticky",
	});

	let segments = $("<div/>", {
		class: "ui raised stacked segments",
	});

	for (const e of htmls) {
		let one = $("<div/>", {
			class: "ui segment",
		});
		one.append(e);
		segments.append(one);
	}

	let text_column = $("<div/>");

	sticker.append(images_grid(keys, source));
	images_column.append(sticker);
	item.append(images_column);
	text_column.append(segments);
	item.append(text_column);
	return item;
}

function all_articles_html(keys_sets_to_articles, source) {
	let item_number = 0;

	let one_big = $("<div/>");

	for (const [k, v] of keys_sets_to_articles) {
		const x = item_html(k, v, item_number, source);
		one_big.append(x);
		++item_number;
	}

	return one_big;
}

function all_data_is_here(article, name_to_tags, tags) {
	// console.log(article[0]);
	// console.log(id_to_name[0]);
	console.log(name_to_tags[0]);
	console.log(tags[0]);
	let source = new cards_data_source();
	let groups = articlesJSON_groupped(article[0], source);
	DOM_append(all_articles_html(groups, source));
}
