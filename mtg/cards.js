"use strict";

class deck_entry {
	constructor(name, count) {
		this.name = name;
		if (!Number.isInteger(count)) {
			throw "Not an integer";
		}
		if (count < 1) {
			throw "Must be at least 1";
		}
		this.count = count;
	}
}

function as_deck_entry(data) {
	if (typeof data === 'deck_entry') {
		return data;
	} else if (typeof data === "string") {
		return new deck_entry(data, 1);
	} else if (data.hasOwnProperty("name") && data.hasOwnProperty("count")) {
		return new deck_entry(data.name, data.count);
	}
	throw "Invalid data format";
}

function as_text_deck(entries) {
	let sorted = Array.from(entries).sort((a, b) => a.name.localeCompare(b.name));
	let text = "";
	for (const e of sorted) {
		text += e.count + " " + e.name + "\n";
	}
	return text;
}

function as_pretty_json(entries) {
	let sorted = Array.from(entries).sort((a, b) => a.name.localeCompare(b.name));
	let text = "";
	text += "[";
	let divider = false;
	for (const e of sorted) {
		if (divider) {
			text += ",";
		} else {
			divider = true;
		}
		text += "\n";
		if (e.count == 1) {
			text += JSON.stringify(e.name);
		} else {
			text += JSON.stringify(e);
		}
	}
	text += "\n]";
	return text;
}