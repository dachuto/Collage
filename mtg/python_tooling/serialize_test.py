import unittest

import serialize

class SerializeTest(unittest.TestCase):
	def test_format(self):
		self.assertEqual(serialize.format_size(), 40)

	def test_exists(self):
		self.assertEqual(serialize.exists_to_binary(None), 0)
		self.assertEqual(serialize.exists_to_binary(0), 1)
		self.assertEqual(serialize.exists_to_binary(1), 1)
		self.assertEqual(serialize.exists_to_binary("arbitrary"), 1)

	def test_to_int(self):
		self.assertEqual(serialize.bits_to_int([]), 0)
		self.assertEqual(serialize.bits_to_int([1, 1, 0, 1, 0, 0, 1, 0]), 75)
		self.assertEqual(serialize.bits_to_int([1, 1, 1, 1, 1, 1, 1, 1]), 255)
		self.assertEqual(serialize.bits_to_int([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]), 1023)
		self.assertRaises(AssertionError, serialize.bits_to_int, [None])
		self.assertRaises(AssertionError, serialize.bits_to_int, [2])

	def test_from_int(self):
		self.assertEqual(serialize.int_to_bits(0), [])
		self.assertEqual(serialize.int_to_bits(41), [1, 0, 0, 1, 0, 1])
		self.assertRaises(AssertionError, serialize.int_to_bits, -1)
		self.assertRaises(TypeError, serialize.int_to_bits, "arbitrary")

	def test_bytes(self):
		d0 = serialize.PriceRecord(1, None, 2.2, 1.1, 3.3, 4.4, None, 1000, 1, 2)
		for i in [d0]:
			with self.subTest(i=i):
				b = serialize.to_bytes(i)
				j = serialize.from_bytes(b)
				self.assertEqual(len(b), serialize.format_size())
				self.assertTrue(serialize.serialized_equality(i, j))

if __name__ == "__main__":
	unittest.main()