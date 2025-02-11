"use strict";

class deck_entry {
	constructor(input) {
		if (!Number.isInteger(input.quantity)) {
			throw "Not an integer";
		}
		if (input.quantity < 1) {
			throw "Must be at least 1";
		}
		if (input.set != null && typeof input.set !== "string") {
			throw "Notes must be string";
		}
		if (input.notes != null && typeof input.notes !== "string") {
			throw "Notes must be string";
		}
		if (input.collector_number != null && typeof input.collector_number !== "string") {
			throw "collector_number not a string";
		}
		if (input.multiverse_id != null && !Number.isInteger(input.multiverse_id)) {
			throw "Not an integer";
		}
		if (input.name == null && (input.multiverse_id == null || (input.set == null || input.collector_number == null))) {
			throw "Not representing any printing";
		}
		if (input.foil != null && typeof input.foil !== "boolean") {
			throw "not a boolean";
		}

		this.name = input.name;

		this.multiverse_id = input.multiverse_id;
		this.set = input.set;
		this.collector_number = input.collector_number;

		this.quantity = input.quantity;

		this.notes = input.notes;
		this.temp_ids = null;

		// if (input.foil == null) {
		// 	this.foil = false;
		// }
		this.foil = input.foil;
	}

	needs_set_printing_fetch() {
		return this.set == null || this.collector_number == null;
	}

	set_fetched_set_printing(set_printing) {
		//TODO: maybe use temp
		this.set = set_printing.set;
		this.collector_number = set_printing.collector_number;
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

	get_set_printing() {
		return {set: this.set, collector_number: this.collector_number};
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
		return new deck_entry({name: data, quantity: 1});
	} else if (typeof data === "number") {
		return new deck_entry({quantity:1, multiverse_id: data});
	} else if (typeof data == "object") {
		return new deck_entry({
			name: property_or_else(data, "name", null),
			quantity: property_or_else(data, "quantity", 1),
			multiverse_id: property_or_else(data, "multiverse_id", null),
			notes: property_or_else(data, "notes", null),
			foil: property_or_else(data, "foil", null),
			set: property_or_else(data, "set", null),
			collector_number: property_or_else(data, "collector_number", null),
		});

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

function as_text_deck_moxfield(entries) {
	const sorted = entries;
	let text = '"Count","Name","Edition","Condition","Language","Foil","Collector Number","Alter","Playtest Card","Purchase Price"';
	for (const e of sorted) {
		text += '"' + e.quantity + '",'
		text += '"' + e.name + '",'
		text += '"' + e.set + '",'
		text += '"Near Mint",'
		text += '"English",'
		text += '"' + (e.foil ? 'foil' : '') + '",'
		text += '"' + e.collector_number + '",'
		text += '"",'
		text += '"",'
		text += '""'
		text += '\n'

	}
	return text;
}

function as_text_deck(entries) {
	const sorted = entries;
	let text = "";
	for (const e of sorted) {
		// 1 Counterspell (CMR) 632 *F*
		text += e.quantity + ' ';
		text += e.name + ' ';
		text += '(' + e.set + ') '
		text += (e.foil ? '*F*' : '') + '\n';
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

	ret["set"] = card.set;
	ret["collector_number"] = card.collector_number;

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
