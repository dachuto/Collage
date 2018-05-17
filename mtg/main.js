"use strict";

class cards_data_source {
	image_url(multiverse_id) {
		return "http://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid=" + multiverse_id
	}
}

function convert_article(article) {
	let re = /([a-z]+)\((.*?)\)/g;

	let tags = new Array();
	function replacer(match, p0, p1, offset, string) {
		tags.push(Number(p1));
		return "XXX"; // TODO: converter id -> html
	}

	return [article.replace(re, replacer), tags];
}

function error_message(h, t) {
	let icon = $("<i/>", {
		class: "exclamation triangle icon"
	});
	let content = $("<div/>", {
		class: "content",
	}).append($("<div/>", {
		class: "header",
		text: h
	})).append($("<p/>", {
		text: t
	}));
	return $("<div>", {
		class: "ui red icon message",
	}).append(icon).append(content);
}

function JSON_request(file_name) {
	let request = $.getJSON(file_name).done(function (data, textStatus, jqXHR) {
		console.log(file_name);
	}).fail(function (jqXHR, textStatus, errorThrown) {
		failed_json(jqXHR, textStatus, errorThrown);

		$("#main_content").append(error_message(file_name, errorThrown));
	});
	return request;
}

function failed_json(jqXHR, textStatus, errorThrown) {
	console.log(jqXHR);
	console.log(textStatus);
	console.log(errorThrown);
}

function DOM_ready() {
	$.when(
		JSON_request("mtg/article.json"),
		JSON_request("mtg/more_data.json"))
	.then(all_data_is_here, null);
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

function articlesJSON_groupped(data) {
	let temp = new Map();

	for (let i in data) {
		let [html, keys] = convert_article(data[i]);
		group_by_keys_set.add(temp, html, keys);
	}
	return group_by_keys_set.get(temp);
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

	let images_grid = $("<div/>", {
		class: "images_grid",
	});

	for (const k in keys) {
		let image = $("<img/>", {
			class: "preview",
			src: source.image_url(k)
		});
		images_grid.append(image);
	}

	let segments = $("<div/>", {
		class: "ui raised stacked segments",
	});

	for (const e of htmls) {
		let one = $("<div/>", {
			class: "ui segment",
			text: e
		});
		segments.append(one);
	}

	let text_column = $("<div/>");

	sticker.append(images_grid);
	images_column.append(sticker);
	item.append(images_column);
	text_column.append(segments);
	item.append(text_column);
	return item;
}

function modify_DOM(keys_sets_to_articles) {
	let source = new cards_data_source();

	let item_number = 0;

	for (const [k, v] of keys_sets_to_articles) {
		const x = item_html(k, v, item_number, source);
		$("#main_content").append(x);
		++item_number;
	}
}

function all_data_is_here(article, more_data) {
	console.log(article[0]);
	let groups = articlesJSON_groupped(article[0]);
	modify_DOM(groups);
	console.log(more_data[0]);
}
