import unittest

import concurrent_do

class test_workers:
	def __init__(self, number_of_jobs, number_of_workers):
		self.number_of_workers = number_of_workers
		self.number_of_jobs = number_of_jobs

	def workers(self):
		for w in range(self.number_of_workers):
			yield "W" + str(w)

	def jobs(self):
		for j in range(self.number_of_jobs):
			yield j

	def parallel_work(self, worker, job):
		print("work ", worker, job)
		return -job

	def merge(self, worker, job, result):
		print("merge", worker, job, result)

	def synchronous_close(self, worker):
		print("close", worker)

class ConcurrentTest(unittest.TestCase):
	def test_format(self):
		w = test_workers(10, 3)
		c = concurrent_do.concurrent_do(w, 2)
		c.start()
		c.close()

if __name__ == "__main__":
	unittest.main()
