import dataclasses
import struct

#import collections
# PriceRecord = collections.namedtuple("price_record", ["multiverse_id", "USD", "USD_foil", "EUR", "EUR_foil", "TIX", "TIX_foil", "year", "month", "day"])

@dataclasses.dataclass
class PriceRecord:
	multiverse_id: int
	USD: float
	USD_foil: float
	EUR: float
	EUR_foil: float
	TIX: float
	TIX_foil: float
	year: int
	month: int
	day: int

	def __getitem__(self, item):
		return [self.multiverse_id, self.USD, self.USD_foil, self.EUR, self.EUR_foil, self.TIX, self.TIX_foil, self.year, self.month, self.day][item]

serialized_format = "!QLffffffHBB" # multiverse_id is followed by a mask showing if prices are there or not

def format_size():
	return struct.calcsize(serialized_format)

def format_mask_length():
	return 6

def exists_to_binary(x):
	return 0 if x is None else 1

def bits_to_int(bits):
	x = 0
	p = 1
	for bit in bits:
		assert bit == 0 or bit == 1
		x += p * bit
		p = p << 1
	return x

def int_to_bits(x):
	bits = []
	assert x >= 0
	while x > 0:
		bits.append(x % 2)
		x = x >> 1
	return bits

def to_bytes(x):
	mask = bits_to_int(exists_to_binary(f) for f in (x[i] for i in range(1, 7)))
	cover_none_float = lambda x: 0.0 if x is None else x
	return struct.pack(serialized_format, x[0], mask, *(cover_none_float(e) for e in x[1:7]), *x[7:])

def from_bytes(bytes):
	u = struct.unpack(serialized_format, bytes)
	mask_bits = int_to_bits(u[1])
	mask_bits = mask_bits + [0] * (format_mask_length() - len(mask_bits))
	reverse_float = lambda i: None if mask_bits[i] == 0 else u[i + 2]
	return PriceRecord(u[0], *(reverse_float(i) for i in range(0, 6)), *u[8:])

def prices_similar(a, b):
	check = lambda x, y: (x is None and y is None) or abs(x - y) < 0.0001
	return all(check(a[i], b[i]) for i in range(1, 7))

def serialized_equality(a, b):
	return a.multiverse_id == b.multiverse_id and a.year == b.year and a.month == b.month and a.day == b.day and prices_similar(a, b)

def from_file(file_name):
	with open(file_name, "rb") as file:
		while True:
			size = format_size()
			read_bytes = file.read(size)
			if (len(read_bytes) != size):
				break
			yield from_bytes(read_bytes)

def to_file(file_name, records):
	with open(file_name, "wb") as file:
		for e in records:
			file.write(to_bytes(e))
