import collections

from xml.etree import ElementTree as ET

DataRow = collections.namedtuple("DataRow", ["good", "price", "value", "name", "foil", "playset", "wanted", "name_fallback", "comments", "date"])

def link_path(file_name):
	common_link_path = '../../third_party/'
	return common_link_path + file_name

def generate_summary(data, max_bar_price=5):
	h = ET.Element('html')
	head = ET.SubElement(h, 'head')
	ET.SubElement(head, 'meta', {'charset':'UTF-8'})
	ET.SubElement(head, 'link', {'rel':'stylesheet', 'type':'text/css', 'href':link_path('datatables.min.css')})
	js_attribs = {'type':'text/javascript', 'charset':'utf8'}
	for script in ['jquery.min.js', 'datatables.min.js']:
		ET.SubElement(head, 'script', {**js_attribs, 'src':link_path(script)})

	ET.SubElement(head, 'script', js_attribs).text = "$(document).ready(function() {let x = $('#table_id').DataTable({" \
		"'pageLength': 100" \
		"}); console.log(x)});"
	body = ET.SubElement(h, 'body')

	table = ET.SubElement(body, 'table', {'id':"table_id", 'class':'display compact'})
	thead = ET.SubElement(table, 'thead')
	h_tr = ET.SubElement(thead, 'tr')
	column_names_tips = [("good", None), ("net", "just price difference"), ("User", "user price"), ("MCM", None), ("€", None), ("f", "is foil"), ("4", "playset"), ("name", None), ("W", "wanted"), ("-", "name fallback"), ("comments", None), ("date", "price check date")]
	for (name, tip) in column_names_tips:
		th = ET.SubElement(h_tr, 'th')
		if tip is None:
			th.text = name
		else:
			ET.SubElement(th, 'abbr', {'title': tip}).text = name

	tbody = ET.SubElement(table, 'tbody')
	for row in data:
		b_tr = ET.SubElement(tbody, 'tr')
		bar = ET.Element('progress', {'data-sort':str(row.price), 'max':str(max_bar_price), 'value':str(row.price)})

		fields = [\
			"{:7.2f}".format(row.good),\
			"{:7.2f}".format(row.value - row.price),\
			"{:7.2f}".format(row.price),\
			"{:7.2f}".format(row.value),\
			bar,\
			"★" if row.foil else "",\
			row.name,
			"④" if row.playset else "",\
			"✔" if row.wanted else "",\
			"?" if row.name_fallback else "",\
			row.comments,\
			row.date\
		]
		for f in fields:
			td = ET.SubElement(b_tr, 'td')
			if type(f) is str:
				td.text = f
			else:
				td.append(f)

		# formats = ["{:7.2f}", "{:7.2f}", "{:7.2f}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}"]
		# playset =
		# foil =
		# wanted =
		# name_fallback =
		# pretty_row = [row.good, row.price, row.value, row.price, foil, playset, row.name, wanted, name_fallback, row.comments, row.date]

		# for (cell, f) in zip(pretty_row, formats):
		# 	ET.SubElement(b_tr, 'td').text = f.format(cell)

	return ET.tostring(h, encoding="unicode", method="html")

if __name__ == "__main__":
	print(generate_summary([DataRow(1, 2, 3, "mcm_csv_name", True, True, True, True, "comments", "date")]))