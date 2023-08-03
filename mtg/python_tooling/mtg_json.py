
class mtg_json:
	def __init__(self):
		self.name_to_multiverse_id = dict()
		# self.name_to_mcm_id = dict()
		self.multiverse_id_to_name = dict()
		# self.multiverse_id_to_mcm_id = dict()
		# self.mcm_id_to_name = dict()
		self.mcm_id_to_multiverse_id = dict()

	def extract(self, data):
		for (set_name, values) in data.items():
			# x = datetime.datetime.strptime(values["releaseDate"], "%Y-%m-%d")
			for v in values["cards"]:
				name = v["name"]
				multiverse_id = v.get("multiverseId", None)
				mcm_id = v.get("mcmId", None)
				if name is None or len(name) == 0:
					raise ValueException("Invalid name")

				if multiverse_id is None and mcm_id is None:
					pass #print("Both ids missing!", name)

				if multiverse_id is not None:
					self.name_to_multiverse_id.setdefault(name, set()).add(multiverse_id)
					self.multiverse_id_to_name.setdefault(multiverse_id, set()).add(name)
					if mcm_id is not None:
						self.mcm_id_to_multiverse_id.setdefault(mcm_id, set()).add(multiverse_id)