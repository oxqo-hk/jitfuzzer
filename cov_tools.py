import numpy as np
class Coverage:
	def __init__(self):
		self.all = []
		self.counter = (0, 0)

	def get_index(self, cov):
		for index, coverage, counter in self.all:
			if coverage == cov:
				return index
		return None

	def add_cov(self, cov):
		self.all.append((len(self.all), cov, 1))
		return self.get_index(cov)

	def count_cov(self, index):
		index, coverage, counter = self.all[index]
		self.all[index] = index, coverage, counter+1

	def get_counter_sum(self):
		ret = 0
		for index, coverage, counter in self.all:
			ret += counter
		return ret

	def get_counter_mul(self):
		ret = 1
		for index, coverage, counter in self.all:
			ret *= counter
		return ret

	def get_length(self):
		return len(self.all)

	def weighted_pick(self):
		counter_mul = self.get_counter_mul()
		weight_sum = 0
		weights = []
		indexes = []
		for index, coverage, counter in self.all:
			indexes.append(index)
			weights.append(np.float64(counter_mul/counter))

		weights = np.array(weights)
		indexes = np.array(indexes)
		weight_sum = np.float64(weights.sum())
		np.multiply(weights, np.divide(np.float64(1), np.float64(weight_sum)), weights)
		return np.random.choice(indexes, 1, p=weights)[0]

	def explored_total(self):
		if len(self.all) == 0:
			return 0
		i, c, count = self.all[0]
		total = len(c.keys())
		explored = list()
		no_check = 0
		for _ in range(total):
			explored.append(0)
		for index, coverage, counter in self.all:
			ex_sum = 0 
			for i, key in enumerate(coverage.keys()):
				if coverage[key] > 0:
					explored[i] = 1
					ex_sum += 1
			if ex_sum == 0:
				no_check = 1

		explored_total = float(sum(explored))
		return ((explored_total+no_check)/(total + 1))

	def get_iteration(self):
		if len(self.all) == 0:
			return 0
		res = 0
		for _, _, counter in self.all:
			res += counter

		return res
