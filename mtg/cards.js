"use strict";

class deck_entry {
	constructor(name, count, ids, notes) {
		if (!Number.isInteger(count)) {
			throw "Not an integer";
		}
		if (count < 1) {
			throw "Must be at least 1";
		}
		if (notes != null && typeof notes !== "string") {
			throw "Notes must be string";
		}

		if (!Array.isArray(ids)) {
			throw "Ids is not an array";
		}

		if (name == null && ids.length < 1) {
			throw "Not representing any printing";
		}

		this.name = name;
		this.count = count;
		this.ids = ids;
		this.notes = notes;
	}
}

function as_deck_entry(data) {
	if (typeof data === 'deck_entry') {
		return data;
	} else if (typeof data === "string") {
		return new deck_entry(data, 1, []);
	} else if (typeof data === "number") {
		return new deck_entry(null, 1, [data]);
	}

	const property_or_else = (object, property, or_else) =>
		object.hasOwnProperty(property) ? object[property] : or_else;

	return new deck_entry(
		property_or_else(data, "name", null),
		property_or_else(data, "count", 1),
		property_or_else(data, "ids", []),
		property_or_else(data, "notes", null)
	);
}

function test() {
	console.debug(as_deck_entry({"ids" : [1], "count" : 2}));
	console.debug(as_deck_entry({"name" : "Island", "notes" : "important stuff"}));
	// console.assert(as_deck_entry("Island") === new deck_entry("Island", 1, [], null));
}

function flat_entries(deck) {
	let flat = [];
	for (const subsection in deck) {
		for (const o in deck[subsection]) {
			flat.push(deck[subsection][o]);
		}
	}
	return flat;
}

function as_text_deck(entries) {
	//let sorted = Array.from(entries).sort((a, b) => a.name.localeCompare(b.name));
	let sorted = entries;
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
