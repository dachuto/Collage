import concurrent.futures

def chain_with_restarts(*iterables):
	while True:
		found = False
		for i in iterables:
			try:
				yield next(i)
				found = True
				break
			except StopIteration:
				pass
		if not found:
			break

class fifo_generator:
	def __init__(self):
		self.stack = []

	def __iter__(self):
		return self

	def __next__(self):
		if self.stack:
			return self.stack.pop()
		else:
			raise StopIteration

	def push(self, x):
		self.stack.append(x)

class concurrent_do:
	def __init__(self, doers, number_of_threads):
		self.doers = doers
		self.executor = concurrent.futures.ThreadPoolExecutor(max_workers = number_of_threads)

	def close(self):
		self.executor.shutdown()

	def schedule_job(self, worker, job):
		return self.executor.submit(lambda w, j: (w, j, self.doers.parallel_work(w, j)), worker, job)

	def start(self):
		workers = self.doers.workers()
		jobs = self.doers.jobs()
		idle_workers = fifo_generator()
		not_done = set()

		def schedule():
			nonlocal workers
			nonlocal jobs
			nonlocal not_done
			nonlocal idle_workers
			for (worker, job) in zip(chain_with_restarts(idle_workers, workers), jobs):
				not_done.add(self.schedule_job(worker, job))

		schedule()

		while not_done:
			done, not_done = concurrent.futures.wait(not_done, timeout=None, return_when=concurrent.futures.FIRST_COMPLETED)
			for future in done:
				worker, job, result = future.result()
				self.doers.merge(worker, job, result)
				idle_workers.push(worker)
				schedule()
