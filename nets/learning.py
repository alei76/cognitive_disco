import numpy as np
import theano
import theano.tensor as T
import timeit

class DataTriplet(object):

	def __init__(self, data_list=None, label_vectors=None):
		self.training_data = []
		self.training_data_label = []
		self.dev_data = []
		self.dev_data_label = []
		self.test_data = []
		self.test_data_label = []

		if data_list is not None:
			self.training_data = [x for x in data_list[0]]
			self.dev_data = [x for x in data_list[1]]
			self.test_data = [x for x in data_list[2]]
		if label_vectors is not None:
			self.training_data_label = [x for x in label_vectors[0]]
			self.dev_data_label = [x for x in label_vectors[1]]
			self.test_data_label = [x for x in label_vectors[2]]

	def _check_num_rows(self, data_list):
		num_rows = [x.shape[0] for x in data_list]
		assert(all(x == num_rows[0] for x in num_rows))

	def assert_data_same_length(self):
		assert(len(self.training_data) == len(self.dev_data))	
		assert(len(self.test_data) == len(self.dev_data))	

		assert(len(self.training_data_label) == len(self.dev_data_label))	
		assert(len(self.test_data_label) == len(self.dev_data_label))	

		self._check_num_rows(self.training_data)
		self._check_num_rows(self.dev_data)
		self._check_num_rows(self.test_data)

		self._check_num_rows(self.training_data_label)
		self._check_num_rows(self.dev_data_label)
		self._check_num_rows(self.test_data_label)

	def num_input_variables(self):
		self.assert_data_same_length()
		return len(self.training_data)

	def input_dimensions(self):
		return [x.shape[1] for x in self.training_data]

	def num_output_variables(self):
		self.assert_data_same_length()
		return len(self.training_data_label)

	def training_data_and_label_list(self):
		return self.training_data + self.training_data_label

	def dev_data_and_label_list(self):
		return self.dev_data + self.dev_data_label

	def test_data_and_label_list(self):
		return self.test_data + self.test_data_label


class Trainer(object):

	def train_minibatch(self, minibatch_size, n_epochs, training_data, dev_data, test_data):
		"""Train minibatch with one output

		training_data should be a list of [X1, X2, ... Xn,Y]
		"""
		data_triplet = DataTriplet()

		data_triplet.training_data.extend(training_data[:-1])
		data_triplet.training_data_label.append(training_data[-1])

		data_triplet.dev_data.extend(dev_data[:-1])
		data_triplet.dev_data_label.append(dev_data[-1])

		data_triplet.test_data.extend(test_data[:-1])
		data_triplet.test_data_label.append(test_data[-1])

		return self.train_minibatch_triplet(minibatch_size, n_epochs, data_triplet)


	def train_minibatch_triplet(self, minibatch_size, n_epochs, data_triplet):
		data_triplet.assert_data_same_length()
		assert(len(self.model.input) == data_triplet.num_input_variables())
		assert(len(self.model.output) == data_triplet.num_output_variables())

		index = T.lscalar() # index to minibatch
		T_training_data = [theano.shared(x, borrow=True) for x in data_triplet.training_data]
		T_training_data_label = [theano.shared(x, borrow=True) for x in data_triplet.training_data_label]

		givens = {}
		for i, output_var in enumerate(self.model.output):
			givens[output_var] = \
				T_training_data_label[i][index * minibatch_size: (index + 1) * minibatch_size]

		for i, input_var in enumerate(self.model.input):
			givens[input_var] = \
				T_training_data[i][index * minibatch_size: (index + 1) * minibatch_size]


		self.train_function = theano.function(
				inputs=[index],
				outputs=self.cost_function,
				updates=self.sgs_updates + self.adagrad_lr_updates + self.param_updates,
				givens=givens
				)

		#cost = theano.function(inputs = [self.model.activation, self.model.output],
				#outputs=self.cost_function)
		accuracy = T.mean(T.eq(self.model.output, self.model.predict))
		self.eval_function = theano.function(inputs=self.model.input + self.model.output,
				outputs=[accuracy, self.cost_function]
				)

		patience = 5000
		patience_increase = 2.5 # wait this much longer when a new best is found
		improvement_threshold = 0.9975

		n_train_batches = data_triplet.training_data[0].shape[0] / minibatch_size
		validation_frequency = min(n_train_batches, patience / 2)
	
		best_validation_loss = np.inf
		test_score = 0 

		done_looping = False
		epoch = 0
		best_dev_acc = 0.0
		best_dev_iteration = 0
		best_test_acc = 0.0
		while (epoch < n_epochs) and (not done_looping):
			epoch = epoch + 1
			for minibatch_index in xrange(n_train_batches):
				iteration = (epoch - 1) * n_train_batches  + minibatch_index
				start_time = timeit.default_timer()
				c = self.train_function(minibatch_index)
				end_time = timeit.default_timer()
				if (iteration + 1) % validation_frequency == 0:
					dev_accuracy, c = \
							self.eval_function(*data_triplet.dev_data_and_label_list())
					print 'DEV: iteration %s : accuracy = %s ; cost =%s' % (iteration, dev_accuracy, c)
					test_accuracy, c = \
							self.eval_function(*data_triplet.test_data_and_label_list())
					print 'TEST: iteration %s : accuracy = %s ; cost =%s' % (iteration, test_accuracy, c)
					if dev_accuracy > best_dev_acc:
						if dev_accuracy * improvement_threshold > best_dev_acc:
							patience = max(patience, iteration * patience_increase)
						best_dev_acc = dev_accuracy
						best_dev_iteration = iteration
						best_test_acc = test_accuracy	
				if patience <= iteration:
					done_looping = True
					break

		return best_dev_iteration, float(best_dev_acc), float(best_test_acc)

class AdagradTrainer(Trainer):

	def __init__(self, model, cost_function, learning_rate, lr_smoother):
		self.model = model
		self.cost_function = cost_function 
		self.learning_rate = learning_rate
		self.lr_smoother = lr_smoother

		gparams = [T.grad(cost=cost_function, wrt=x) for x in self.model.params]
		adagrad_rates = [theano.shared(value=np.zeros(param.get_value().shape)) 
				for param in self.model.params]
		sum_gradient_squareds = [theano.shared(value=np.zeros(param.get_value().shape)) 
				for param in self.model.params]

		self.sgs_updates = [(sgs, sgs + T.square(gparam)) 
			for sgs, gparam in zip(sum_gradient_squareds, gparams)]

		self.adagrad_lr_updates = [(adagrad_rate, 
			adagrad_rate + learning_rate / (lr_smoother + T.sqrt(sum_gradient_squared)))
			for adagrad_rate, sum_gradient_squared in zip(adagrad_rates, sum_gradient_squareds)]

		self.param_updates = [(param, param - adagrad_rate * gparam) 
				for param, gparam, adagrad_rate in zip(self.model.params, gparams, adagrad_rates)]



class SGDTrainer(Trainer):

	def __init__(self, model, cost_function, learning_rate):
		self.model = model
		self.cost_function = cost_function 
		self.learning_rate = learning_rate

		gparams = [T.grad(cost=cost_function, wrt=x) for x in self.model.params]

