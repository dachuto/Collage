"use strict";

class deck_entry {
	constructor(name, quantity, multiverse_id, notes, foil) {
		if (!Number.isInteger(quantity)) {
			throw "Not an integer";
		}
		if (quantity < 1) {
			throw "Must be at least 1";
		}
		if (notes != null && typeof notes !== "string") {
			throw "Notes must be string";
		}

		if (multiverse_id != null && !Number.isInteger(multiverse_id)) {
			throw "Not an integer";
		}
		// if (ids != null && !Array.isArray(ids)) {
		// 	throw "Ids is not an array";
		// }

		if (name == null && multiverse_id == null) {
			throw "Not representing any printing";
		}

		if (foil != null && typeof foil !== "boolean") {
			throw "not a boolean";
		}

		this.name = name;
		this.quantity = quantity;
		this.multiverse_id = multiverse_id;
		this.notes = notes;
		this.temp_ids = null;
		if (foil == null) {
			this.foil = false;
		}
		this.foil = foil;
	}

	needs_multiverse_id_fetch() {
		return this.multiverse_id == null;
	}

	set_fetched_multiverse_ids(ids) {
		if (ids == null) {
			throw "null provided" + this.name;
		}

		if (this.multiverse_id != null) {
			throw "Overwriting ids";
		}
		this.temp_ids = ids;
	}

	get_single_multiverse_id() {
		if (this.multiverse_id != null) {
			return this.multiverse_id;
		}

		if (this.temp_ids == null) {
			throw "no ids to work with ";
		}
		return this.temp_ids.at(-1);
	}
}

function as_deck_entry(data) {
	const property_or_else = (object, property, or_else) =>
		object.hasOwnProperty(property) ? object[property] : or_else;

	if (typeof data === 'deck_entry') {
		return data;
	} else if (typeof data === "string") {
		return new deck_entry(data, 1, null, null, false);
	} else if (typeof data === "number") {
		return new deck_entry(null, 1, data, null, false);
	} else if (typeof data == "object") {
		return new deck_entry(
			property_or_else(data, "name", null),
			property_or_else(data, "quantity", 1),
			property_or_else(data, "multiverse_id", null),
			property_or_else(data, "notes", null),
			property_or_else(data, "foil", null),
		);

		return new deck_entry(data["name"], parseInt(data["quantity"]), [data["multiverse_id"]], data["foil"]);
	} else {
		console.log(data);
		throw "Unknown entry"
	}
}

function test() {
	//TODO
	// console.debug(as_deck_entry({"ids" : [1], "count" : 2}));
	// console.debug(as_deck_entry({"name" : "Island", "notes" : "important stuff"}));
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
		text += e.quantity + " " + e.name + "\n";
	}
	return text;
}

function as_json_string(card) {
	const ret = {};
	if (card.name != null) {
		ret["name"] = card.name;
	}
	if (card.quantity > 1) {
		ret["quantity"] = card.quantity;
	}
	const multiverse_id = card.get_single_multiverse_id();
	if (multiverse_id != null) {
		ret["multiverse_id"] = multiverse_id;
	}
	if (card.foil) {
		ret["foil"] = true;
	}
	if (card.notes != null) {
		ret["notes"] = card.notes;
	}

	return JSON.stringify(ret);
}

function as_pretty_json(entries) {
	// let sorted = Array.from(entries).sort((a, b) => a.name.localeCompare(b.name));
	let text = "";
	text += "[";
	let divider = false;
	for (const e of entries) {
		if (divider) {
			text += ",";
		} else {
			divider = true;
		}
		text += "\n";
		text += as_json_string(e);
	}
	text += "\n]";
	return text;
}
