"use strict";

// function convert_article(article, source) {
// 	let re = /#([a-z]+)\((.*?)\)/g;

// 	let tags = new Array();
// 	function replacer(match, p0, p1, offset, string) {
// 		tags.push(Number(p1));
// 		return source.id_to_html(p1);
// 	}

// 	return [$.parseHTML(article.replace(re, replacer)), tags];
// }

function error_message_html(header, inside) {
	const top = document.createElement("div");
	top.classList.add("ui", "red", "icon", "message");
	const ico = document.createElement("i");
	ico.classList.add("exclamation", "triangle", "icon");
	const d = document.createElement("div");
	d.classList.add("content");
	const dd = document.createElement("div");
	dd.classList.add("header");
	dd.textContent = String(header);
	const pp = document.createElement("p");
	pp.textContent = String(inside);
	top.appendChild(ico);
	top.appendChild(d);
	d.appendChild(dd);
	d.appendChild(pp);
	return top;
}

async function JSON_request(file_name) {
	const response = await fetch(file_name);
	if (!response.ok) {
		DOM_append(error_message_html(file_name, response.statusText));
		return Promise.reject(response.statusText);
	}

	try {
		const json = await response.json();
		return json;
	} catch (error) {
		DOM_append(error_message_html(file_name, error));
	}
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
	DFS(graph, undefined, () => { }, (v) => {
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
		inner.className = "";
		inner.classList.add("card_tag_inner", this.css_class());
	}
}

class page_data {
	constructor() {
		this.backend_url = new URL("http://localhost:8080");
		this.images_info = { loaded: 0, total: 0 };
		this.message_box = document.querySelector("#message_box");
		this.message_box_timer = null;
		this.source = {
			scryfall_single_link: card => {
				return "https://scryfall.com/card/" + card.set.toLowerCase() + "/" + card.collector_number.toString();

			},

			image_url: set_printing => {
				return "http://localhost:2345" + "/" + set_printing.set.toLowerCase() + "/" + set_printing.collector_number.toString();
			},

			scryfall_all_prints_link: card => {
				return "https://scryfall.com/search?as=grid&order=released&q=%21%22" + card.name + "%22+include%3Aextras&unique=prints";
			}

			// image_url: multiverse_id => {
			// 	// return "https://api.scryfall.com/cards/multiverse/" + multiverse_id + "?format=image";
			// 	return "https://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid=" + multiverse_id;
			// },
		}

		this.search_button = document.getElementById("search_button");
		this.search_input = document.getElementById("search_input");

		this.card_search_input = document.getElementById("card_search_input");
		this.card_search_preview = document.getElementById("card_search_preview");
		this.temp_deck_display_content = document.getElementById("temp_deck_display_content");

		this.temp_deck = []
		window.onbeforeunload = event => { if (this.temp_deck.length > 0) { event.preventDefault(); } };

		this.search_input.value = window.location.search;
		this.search_button.onclick = () => {
			// console.log(encodeURIComponent(SI.value));
			// data.start_async_loading();
			// window.history.pushState(null, "", "http://localhost:1234/mtg_results.html?set=BBD");
			// window.history.replaceState(null, "", "http://localhost:1234/mtg_results.html?set=BBD");
		};

		this.commander_deck_param = "deck";
		this.commander_decks = new Map();
		this.commander_decks.set("COLLECTION", "collection.json");
		this.commander_decks.set("WANTS", "wants.json");
		this.commander_decks.set("Ideas - Niv Mizzet", "ideas/commander_niv_mizzet.json");
		this.commander_decks.set("Ideas - Shirei", "ideas/commander_shirei.json");
		this.commander_decks.set("Ideas - Omnath 5c", "ideas/commander_omnath_5c.json");
		this.commander_decks.set("Ideas - Meria Gruul Artifacts", "ideas/commander_meria.json");
		this.commander_decks.set("Twincasters tokens", "commander_twincasters_tokens.json");
		this.commander_decks.set("* counters deck", "commander_counters.json");
		this.commander_decks.set("Nymris instant trickery", "commander_nymris_instants.json");
		this.commander_decks.set("artifacts Esper", "commander_artifacts.json");
		this.commander_decks.set("curses Mardu", "commander_curses.json");
		this.commander_decks.set("cycling *", "commander_cycling.json");
		this.commander_decks.set("equipment White", "commander_equipment.json");
		this.commander_decks.set("Estrid", "commander_estrid.json");
		this.commander_decks.set("flying*", "commander_flying.json");
		this.commander_decks.set("Firesong *", "commander_firesong.json");
		this.commander_decks.set("Sevinne - Flashback", "commander_flashback.json");
		this.commander_decks.set("Henzie", "commander_henize.json");
		this.commander_decks.set("Kadena *", "commander_kadena.json");
		this.commander_decks.set("Kathril keyword soup", "commander_kathril.json");
		this.commander_decks.set("Merieke Ri Berit", "commander_merieke.json");
		this.commander_decks.set("Minn", "commander_minn.json");
		this.commander_decks.set("Nin, the Pain Artist", "commander_nin.json");
		this.commander_decks.set("populate *", "commander_populate.json");
		this.commander_decks.set("Roon", "commander_roon.json");
		this.commander_decks.set("season of growth *", "commander_season_of_growth.json");
		this.commander_decks.set("Quintorius", "commander_quintorius.json");
		this.commander_decks.set("Taigam", "commander_taigam.json");
		this.commander_decks.set("takeover", "commander_takeover.json");
		this.commander_decks.set("Tatsunari", "commander_tatsunari.json");
		this.commander_decks.set("Wort", "commander_wort.json");
		this.commander_decks.set("Mill", "commander_mill_grixis.json");
		this.commander_decks.set("--FOG", "commander_fog.json");
		this.commander_decks.set("CUBE", "cube.json");

		this.commander_decks.set("DISCARDED Combo Golos", "ideas/commander_combo.json");
		//UPDATED recently
		this.commander_decks.set("Grenzo", "commander_grenzo.json");
		this.commander_decks.set("Teysa", "commander_teysa.json");
		this.commander_default_deck = this.commander_decks.keys().next().value;
		this.json_path_prefix = "mtg/articles/";
	}

	validate_url(url) {
		const url_params = new URLSearchParams(url.search);

		if (!url_params.has(this.commander_deck_param)) {
			url_params.append(this.commander_deck_param, this.commander_default_deck);
		}

		const modified_url = new URL(url);
		modified_url.search = url_params;

		// console.log(modified_url);
		const json_path = this.json_path_prefix + this.commander_decks.get(url_params.get(this.commander_deck_param));
		return [modified_url, json_path];
	}

	add_custom_overlay(card, overlay) {
		if (true) {
			const x = (card.quantity > 1) ? card.quantity.toString() : "";
			const number_of_copies_overlay = square_text_svg(x);
			number_of_copies_overlay.classList.add("transparent-barely-visible", "svg-opacity-aid");
			overlay.appendChild(number_of_copies_overlay);
		}

		if (true) {
			const number_of_copies_overlay = list_svg();
			number_of_copies_overlay.classList.add("transparent-barely-visible", "svg-opacity-aid");
			overlay.appendChild(number_of_copies_overlay);
		}

		if (true) {
			const sf_link = document.createElement("a");
			const s = square_text_svg_adjusted("SF");
			sf_link.classList.add("transparent-barely-visible", "svg-opacity-aid");
			sf_link.setAttribute("href", this.source.scryfall_all_prints_link(card));
			sf_link.appendChild(s);
			overlay.appendChild(sf_link);
		}

		if (true) {
			const sf_link = document.createElement("a");
			const s = square_text_svg_adjusted("🂡");
			sf_link.classList.add("transparent-barely-visible", "svg-opacity-aid");
			sf_link.setAttribute("href", this.source.scryfall_single_link(card));
			sf_link.appendChild(s);
			overlay.appendChild(sf_link);
		}
		if (true) {
			const prices = this.search_for_prices(card);
			if (prices !== undefined) {

				const price_string = (maybe_value, currency) => {
					if (maybe_value === undefined) {
						return "";
					}
					return currency + maybe_value.toFixed(2);
				};

				const all_four = [
					price_string(prices.tcgnormal, "$"),
					price_string(prices.mkmnormal, "€"),
					price_string(prices.tcgfoil, "$"),
					price_string(prices.mkmfoil, "€"),
				];

				all_four.forEach((text_value, index) => {
					const element = square_text_svg_adjusted(text_value);
					element.classList.add("transparent-almost-opaque", "svg-opacity-aid", "card-grid-prices-position-" + index);
					overlay.appendChild(element);
				});
			}
		}
	}

	main_images_grid(deck) {
		let images_grid = document.createElement("div");
		images_grid.classList.add("images_grid");

		for (const card of deck) {
			const [card_div, overlay] = create_card_div(card, this.source);
			this.add_custom_overlay(card, overlay);

			images_grid.appendChild(card_div);
		}

		return images_grid;
	}

	preview_images_grid(deck) {
		let images_grid = document.createElement("div");
		images_grid.classList.add("images_grid");

		for (const card of deck) {
			const [card_div, overlay] = create_card_div(card, this.source);
			this.add_custom_overlay(card, overlay);
			images_grid.appendChild(card_div);
			card_div.onclick = (event) => {
				const add_foil = document.getElementById("card_preview_add_foil_checkbox").checked;
				card.foil = add_foil;
				this.temp_deck.push(card);
				temp_deck_display_content.replaceChildren(this.main_images_grid(this.temp_deck));

				this.card_search_input.value = "";
				this.card_search_input.focus();
			};
		}

		return images_grid;
	}

	populate_decks_list() {
		const menu = document.getElementById("commander_decks_menu");
		let counter = 1;
		for (const [key, value] of this.commander_decks) {
			const commander_deck_link = new URL(window.location);
			commander_deck_link.search = new URLSearchParams([[this.commander_deck_param, key]]);

			let inner = document.createElement("a");
			inner.classList.add("item");
			inner.setAttribute("href", commander_deck_link);
			inner.textContent = counter + ". " + key;
			menu.appendChild(inner);
			++counter;
		}
	}

	deck_page_init() {
		const [modified_url, json_path] = this.validate_url(window.location);
		history.replaceState(null, null, modified_url);

		this.populate_decks_list();

		JSON_request(json_path).then(deck => {
			for (const subsection in deck) {
				deck[subsection] = deck[subsection].map(as_deck_entry);
			}

			const cards = flat_entries(deck);
			this.add_colors_and_icons(deck);
			this.deck = deck;

			this.request_missing_card_names(cards)
				.then(values => this.fetch_card_name_to_multiverse_id())
				.then(values => this.fetch_card_name_to_set_printing())
				.then(values => this.fetch_set_printing_to_prices())
				.then(values => this.fetch_multiverse_id_to_set_printing())
				.then(values => {
					cards.forEach(card => this.fill_card_set_printing_based_on_multiverse_id(card));
					cards.forEach(card => this.fill_card_set_printing_based_on_name(card));
					//this.fill_card_multiverse_id_based_on_name(cards);
					this.fill_deck_text_boxes(cards);
					document.getElementById("main_content").replaceChildren(this.main_images_grid(cards));
					this.card_search_input.onchange = event => this.search_event(event);
				});
		});
	}

	fill_deck_text_boxes(cards) {
		document.getElementById("deck_text").textContent = as_text_deck(cards);
		document.getElementById("deck_select_button").onclick = select_element_by_id("deck_text");
		document.getElementById("json_fill_button").onclick = () => {
			document.getElementById("json_text").textContent = as_pretty_json(this.temp_deck);
			// document.getElementById("json_text").textContent = as_pretty_json(this.deck["main"]);
		}
		document.getElementById("json_select_button").onclick = select_element_by_id("json_text");
	}

	fetch_card_name_to_set_printing() {
		const all_url = new URL("/query", this.backend_url);
		all_url.search = "card_name_to_set_printing=";
		return JSON_request(all_url.href).then(value => {
			this.card_name_to_set_printing = value;
			this.fuse = new Fuse(Object.keys(this.card_name_to_set_printing), {
				// includeScore: true,
				isCaseSensitive: false,
				threshold: 0.5
			});
			this.search_for_name_matches = (name) => {
				return this.fuse.search(name).map(e => e.item);
			};
		});
	}

	fetch_set_printing_to_prices() {
		const all_url = new URL("/query", this.backend_url);
		all_url.search = "set_printing_to_prices=";
		return JSON_request(all_url.href).then(value => {
			this.set_printing_to_prices = value;
			this.search_for_prices = (card) => {
				return this.set_printing_to_prices[card.set + "/" + card.collector_number];
			};
		});
	}

	fetch_multiverse_id_to_set_printing() {
		const all_url = new URL("/query", this.backend_url);
		all_url.search = "multiverse_id_to_set_printing=";
		return JSON_request(all_url.href).then(value => {
			this.multiverse_id_to_set_printing = value;
		});
	}

	fetch_card_name_to_multiverse_id() {
		//TODO: do we use this anymore?
		const all_url = new URL("/query", this.backend_url);
		all_url.search = "card_name_to_multiverse_id=";

		return JSON_request(all_url.href).then(value => {
			this.card_name_to_multiverse_id = value;
		});
	}

	search_event(event) {
		console.log(event);
		const needle = this.card_search_input.value;

		const MAX_PREVIEWED_UNIQUE_CARDS = 8;
		const cards_to_preview = this.search_for_name_matches(needle)
			.slice(0, MAX_PREVIEWED_UNIQUE_CARDS)
			.flatMap(name => this.card_name_to_set_printing[name].map(set_printing => new deck_entry({ name: name, quantity: 1, set: set_printing.set, collector_number: set_printing.collector_number })));

		// this.fill_card_multiverse_id_based_on_name(cards_to_preview);
		console.log(cards_to_preview);
		this.card_search_preview.replaceChildren(this.preview_images_grid(cards_to_preview));
	}

	add_colors_and_icons(deck) {
		const count_cards = (entries) => entries.reduce((accumulator, value) => accumulator + value.quantity, 0);

		const subsection_to_icon = {
			"commander": ["star"],
			"main": ["file"],
			"sideboard": ["exchange"],
			"wants": ["cart", "plus"]
		};

		const ui_icon = subsection => {
			const ret = subsection_to_icon[subsection];
			if (ret !== undefined) {
				return ret;
			} else {
				return ["file", "outline"];
			}
		};

		let colors = {};
		if (deck.hasOwnProperty("commander")) {
			colors.commander = "red";
			if (deck.hasOwnProperty("main")) {
				colors.main = "red";
				if (count_cards(deck["commander"]) + count_cards(deck["main"]) == 100) {
					colors.commander = "green";
					colors.main = "green";
				}
			}
		} else if (deck.hasOwnProperty("main")) {
			colors.main = "red";
			if (count_cards(deck["main"]) == 60) {
				colors.main = "green";
			}

			if (deck.hasOwnProperty("sideboard")) {
				colors.sideboard = "red";
				if (count_cards(deck["sideboard"]) == 15) {
					colors.sideboard = "green";
				}
			}
		}

		for (const subsection in deck) {
			const color = (colors[subsection] === undefined) ? "blue" : colors[subsection];
			document.getElementById("deck_subsection_menu").appendChild(deck_subsection_menu_item(subsection, "TODO", count_cards(deck[subsection]), ui_icon(subsection), color));
		}
	}

	request_missing_card_names(cards) {
		let requests = [];
		for (const card of cards) {
			if (card.name != null) {
				continue;
			}
			let url = new URL("/query", this.backend_url);
			url.search = "multiverse_id=" + card.get_single_multiverse_id();
			requests.push(JSON_request(url.href).then(
				value => { card.name = value; }
			));
		}

		return Promise.all(requests);
	}

	fill_card_set_printing_based_on_name(card) {
		if (!card.needs_set_printing_fetch()) {
			return;
		}
		if (card.name == null) {
			return;
		}

		console.log(card);
		const printing = this.card_name_to_set_printing[card.name][0];
		if (printing === undefined) {
			console.log("Suspicious name: " + card);
		} else {
			card.set_fetched_set_printing(this.card_name_to_set_printing[card.name][0]);
		}

	}

	fill_card_set_printing_based_on_multiverse_id(card) {
		if (!card.needs_set_printing_fetch()) {
			return;
		}

		const multiverse_id = card.multiverse_id;
		if (multiverse_id == null) {
			return;
		}

		const printing = this.multiverse_id_to_set_printing[multiverse_id];
		if (printing === undefined) {
			console.log("Suspicious multiverse_id: " + multiverse_id);
		} else {
			card.set_fetched_set_printing(printing);
		}
	}

	fill_card_multiverse_id_based_on_name(cards) { // DEPRECATED: do not call this unless you have a good reason to
		for (const card of cards) {
			if (!card.needs_multiverse_id_fetch()) {
				continue;
			}

			let multiverse_ids = this.card_name_to_multiverse_id[card.name];
			if (multiverse_ids == null) {
				const replacement = this.search_for_name_matches(card.name)[0];
				console.log("! " + card.name + " -> " + replacement);
				card.name = replacement;
				multiverse_ids = this.card_name_to_multiverse_id[card.name];
			}

			card.set_fetched_multiverse_ids(multiverse_ids);
		}
	}

	// async_complete(info, query) {
	// 	console.log(":ASDADAS");
	// 	this.append_images_grid(query[0]);
	// }

	// start_lazy_images_loading() {
	// 	let options = {
	// 		root: null,
	// 		rootMargin: '150%',
	// 		threshold: [0.0]
	// 	};

	// 	let observer = new IntersectionObserver((entries, observer) => {
	// 		for (const e of entries) {
	// 			if (e.isIntersecting) {
	// 				image_load(e.target);
	// 				++this.images_info.loaded;
	// 				this.update_message_box();
	// 				observer.unobserve(e.target);
	// 			}
	// 		}
	// 	}, options);

	// 	for (const target of document.querySelectorAll(".lazy_load_when_almost_visible")) {
	// 		++this.images_info.total;
	// 		observer.observe(target);
	// 	}
	// }

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

// function DOM_ready() {
// 	$.when(
// 		JSON_request("mtg/article.json"),
// 		JSON_request("mtg/name_to_tag.json"),
// 		JSON_request("mtg/tags.json")
// 	).then(all_data_is_here, null);
// }

function DOM_ready_wants() {
	let data = new page_data();
	data.deck_page_init();
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

// function DOM_ready_results() {
// 	document.addEventListener("keyup", event => { //TODO: handle keys to do simple searches
// 		console.log(event);
// 		// if (event.key !== "Enter") return; // Use `.key` instead.
// 		// document.querySelector("#linkadd").click(); // Things you want to do.
// 		event.preventDefault(); // No need to `return false;`.
// 	});
// 	let data = new page_data();
// 	data.start_async_loading();
// }

function DOM_append(element) {
	document.getElementById("main_content").append(element);
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

// function articlesJSON_groupped(data, source) {
// 	let temp = new Map();

// 	for (let i in data) {
// 		let [html, keys] = convert_article(data[i], source);
// 		group_by_keys_set.add(temp, html, keys);
// 	}
// 	return group_by_keys_set.get(temp);
// }

function deck_subsection_menu_item(name, url, count, ui_icon_names, color) {
	let a = document.createElement("a");
	a.classList.add("item");
	a.setAttribute("href", url);

	let icon = document.createElement("i");
	icon.classList.add(...ui_icon_names);
	icon.classList.add("icon");

	let text = document.createTextNode(name);

	let label = document.createElement("div");
	label.classList.add("ui", "left", "pointing", color, "basic", "label");
	label.textContent = count;

	a.appendChild(icon);
	a.appendChild(text);
	a.appendChild(label);
	return a;
}

function square_text_svg_advanced(text_content, text_size) {
	let svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
	svg.setAttribute("viewBox", "0 0 100 100");
	let text = document.createElementNS(svg.namespaceURI, "text");
	text.setAttribute("dominant-baseline", "central");
	text.setAttribute("text-anchor", "middle");
	text.setAttribute("text-align", "center");
	text.setAttribute("font-size", text_size.toString());
	text.setAttribute("x", "50%");
	text.setAttribute("y", "50%");
	text.textContent = text_content;

	svg.appendChild(text);
	return svg;
}

function square_text_svg_adjusted(text_content) {
	const adjusted_size = 160.0 / text_content.length;
	return square_text_svg_advanced(text_content, adjusted_size);
}


function square_text_svg(text_content) {
	return square_text_svg_advanced(text_content, 80);
}

function list_svg() {
	let svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
	svg.setAttribute("viewBox", "0 0 24 24");
	let path_0 = document.createElementNS(svg.namespaceURI, "path");
	let path_1 = document.createElementNS(svg.namespaceURI, "path");
	path_0.setAttribute("d", "M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z");
	path_1.setAttribute("fill", "none");
	svg.appendChild(path_0);
	svg.appendChild(path_1);
	return svg;
}

function list_overlay(hover_node, hidden_node, images_to_lazy_load) {
	const TRANSPARENT_STYLES = ["transparent-fully", "transparent-barely-visible", "transparent-almost-opaque"];
	let list_overlay = list_svg();
	list_overlay.classList.add("card-overlay");
	//TODO: now grid - does not need positioning, especially built-in
	// list_overlay.classList.add("list-overlay-position");
	list_overlay.classList.add("opacity-transition");
	list_overlay.classList.add(TRANSPARENT_STYLES[0]);

	hover_node.onmouseenter = function () {
		list_overlay.classList.add(TRANSPARENT_STYLES[1]);
	};
	hover_node.onmouseleave = function () {
		list_overlay.classList.remove(TRANSPARENT_STYLES[1]);
	};

	const make_visible = function () {
		list_overlay.classList.add(TRANSPARENT_STYLES[2]);
		hidden_node.classList.remove("invisible");
	};

	const lazy_load = function () { //TODO: replace this with built-in lazy load
		for (const image of images_to_lazy_load) {
			image_load(image);
		}
	};

	list_overlay.onmouseenter = function () {
		lazy_load();
		make_visible();
		list_overlay.onmouseenter = make_visible;
	};

	list_overlay.onmouseleave = function () {
		list_overlay.classList.remove(TRANSPARENT_STYLES[2]);
		hidden_node.classList.add("invisible");
	};

	return list_overlay;
}

function image_not_loaded_html(url) {
	let i = document.createElement("div");
	i.classList.add("aspect-ratio-box-inside", "image-inactive", "transparent-almost-opaque");
	i.setAttribute("data-src", url);
	return i;
}

// function image_load(placeholder) {
// 	let image = image_loaded_html(placeholder.getAttribute("data-src"));
// 	if (true) {
// 		placeholder.insertAdjacentElement('afterend', image);
// 	} else {
// 		const parent = placeholder.parentNode;
// 		parent.replaceChild(image, placeholder);
// 	}
// }

function image_loaded_html(src) {
	const image = document.createElement("img");
	image.setAttribute("loading", "lazy");
	image.classList.add("aspect-ratio-box-inside", "preview");
	image.setAttribute("src", src);
	return image;
}

function image_background() {
	const b = document.createElement("div");
	b.classList.add("aspect-ratio-box-inside", "image-inactive");
	return b;
}

function create_card_div(card, source) {
	const card_container = document.createElement("div");
	card_container.classList.add("aspect-ratio-box");

	const image_container = document.createElement("div");

	// const image = image_not_loaded_html(source.image_url(id));
	const image = image_loaded_html(source.image_url(card.get_set_printing()));
	image_container.appendChild(image_background());
	image_container.appendChild(image);

	const overlay = document.createElement("div");
	overlay.classList.add("card-grid");

	const hidden_name = document.createElement("div");
	hidden_name.textContent = card.name;
	hidden_name.classList.add("card-name-hidden");
	image_container.appendChild(hidden_name);

	card_container.appendChild(image_container);
	card_container.appendChild(overlay);


	// 	if (k == chosen_index) {

	// 		if (entry.quantity != 1) {
	// 			let number_of_copies_overlay = square_text_svg(entry.quantity.toString());
	// 			number_of_copies_overlay.classList.add("transparent-barely-visible");
	// 			overlay.appendChild(number_of_copies_overlay);
	// 		}

	// 	} else {
	// 		secondary_images.push(image);
	// 		hidden_printings.appendChild(image_container);
	// 	}
	// }

	// const chosen_index = entry.ids.length - 1; //TODO: we take last (newest printing), maybe customize
	// let hidden_printings = null;
	// const hide_some_printings = (entry.ids.length > 1);
	// if (hide_some_printings) {
	// 	hidden_printings = document.createElement("div");
	// 	hidden_printings.classList.add("fullscreen", "images_grid", "popup", "invisible");
	// }

	// let secondary_images = [];

	// secondary_images.splice(0, secondary_images.length - 16); // trim the number of printings previewed

	// if (hidden_printings !== null) {
	// 	// TODO: scryfall link should be much better
	// 	// overlay.appendChild(list_overlay(overlay, hidden_printings, secondary_images));
	// 	// overlay.appendChild(hidden_printings);
	// }
	return [card_container, overlay];
}

// function item_html(keys, htmls, item_number, source) {
// 	let item = $("<div/>", {
// 		class: "article_grid"
// 	});

// 	let images_column = $("<div/>", {
// 		class: "images_column"
// 	});

// 	let sticker = $("<div/>", {
// 		class: "top_sticky",
// 	});

// 	let segments = $("<div/>", {
// 		class: "ui raised stacked segments",
// 	});

// 	for (const e of htmls) {
// 		let one = $("<div/>", {
// 			class: "ui segment",
// 		});
// 		one.append(e);
// 		segments.append(one);
// 	}

// 	let text_column = $("<div/>");

// 	sticker.append(main_images_grid(keys, source));
// 	images_column.append(sticker);
// 	item.append(images_column);
// 	text_column.append(segments);
// 	item.append(text_column);
// 	return item;
// }

// function all_articles_html(keys_sets_to_articles, source) {
// 	let item_number = 0;

// 	let one_big = $("<div/>");

// 	for (const [k, v] of keys_sets_to_articles) {
// 		const x = item_html(k, v, item_number, source);
// 		one_big.append(x);
// 		++item_number;
// 	}

// 	return one_big;
// }

// function all_data_is_here(article, name_to_tags, tags) {
// 	// console.log(article[0]);
// 	// console.log(id_to_name[0]);
// 	console.log(name_to_tags[0]);
// 	console.log(tags[0]);
// 	let source = new cards_data_source();
// 	let groups = articlesJSON_groupped(article[0], source);
// 	DOM_append(all_articles_html(groups, source));
// }
