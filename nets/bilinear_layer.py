import numpy as np
import scipy as sp
import theano
import theano.sparse
import theano.tensor as T
import timeit

from learning import AdagradTrainer

class LinearLayer(object):
	"""Linear Layer that supports multiple separate input (sparse) vectors

	"""

	def __init__(self, rng, n_in_list, n_out, use_sparse, X_list=None, Y=None, 
			W_list=None, b=None, activation_fn=T.tanh):
		if W_list is None:
			W_list = []
			total_n_in = np.sum(n_in_list)
			for n_in in n_in_list:
				W_values = np.asarray(
					rng.uniform(
						low=-np.sqrt(6. / (total_n_in + n_out)),
						high=np.sqrt(6. / (total_n_in + n_out)),
						size=(n_in, n_out)
					),
					dtype=theano.config.floatX
				)
				W = theano.shared(value=W_values, borrow=True)
				W_list.append(W)
		if b is None:
			b_values = np.zeros((n_out,), dtype=theano.config.floatX)
			b = theano.shared(value=b_values, borrow=True)

		if X_list is None:
			if use_sparse:
				self.input = [theano.sparse.csr_matrix() for i in xrange(len(n_in_list))]
			else:
				self.input = [T.matrix() for i in xrange(len(n_in_list))]
		else:
			assert(len(X_list) == len(n_in_list))
			self.input = X_list

		self.W_list = W_list
		self.b = b
		self.params = self.W_list + [self.b]
		
		if use_sparse:
			net = self.b + theano.sparse.structured_dot(self.input[0], self.W_list[0])
			for i in range(1, len(self.input)):
				net += theano.sparse.structured_dot(self.input[i],self.W_list[i])
		else:
			net = self.b + T.dot(self.input[0], self.W_list[0])
			for i in range(1, len(self.input)):
				net += T.dot(self.input[i], self.W_list[i])
		
		self.activation = (
			net if activation_fn is None
			else activation_fn(net)
		)

		if Y is None:
			self.output = [self.activation]
		else:
			self.output = [Y]
			self.predict = self.activation.argmax(1)
			hinge_loss_instance, _ = theano.scan(
					lambda a, y: T.maximum(0, 1 - a[y] + a).sum() - 1 ,
					sequences=[self.activation, Y])
			self.hinge_loss = hinge_loss_instance.sum()
			self.crossentropy = -T.mean(self.activation[T.arange(Y.shape[0]), Y])



class BilinearLayer(object):

	def __init__(self, rng, n_in1, n_in2, n_out, W=None, b=None, activation_fn=T.tanh):
		if W is None:
			W_values = np.asarray(
				rng.uniform(
					low=-np.sqrt(6. / (n_in1 + n_in2 + n_out)),
					high=np.sqrt(6. / (n_in1 + n_in2 + n_out)),
					size=(n_out, n_in1, n_in2)
				),
				dtype=theano.config.floatX
			)
			W = theano.shared(value=W_values, name='W', borrow=True)
		
		if b is None:
			b_values = np.zeros((n_out,), dtype=theano.config.floatX)
			b = theano.shared(value=b_values, name='b', borrow=True)
		
		self.X1 = T.matrix('x1')
		self.X2 = T.matrix('x2')
		self.Y = T.lvector('y')
		self.W = W
		self.b = b
		self.input = [self.X1, self.X2]
		self.output = [self.Y]
		self.params = [self.W, self.b]
		net, _ = theano.scan(
				lambda x1, x2: T.dot(T.dot(x1, self.W),x2.T) + self.b,
				sequences=[self.X1, self.X2]
			)


		self.activation = (
			net if activation_fn is None
			else activation_fn(net)
		)
		self.predict = self.activation.argmax(1)

		hinge_loss_instance, _ = theano.scan(
				lambda a, y: T.maximum(0, 1 - a[y] + a).sum() - 1 ,
				sequences=[self.activation, self.Y])
		self.hinge_loss = hinge_loss_instance.sum()

		true_label_activation, _ = theano.scan(
				lambda a, y: T.log(1 - a[y]), 
				sequences=[self.activation, self.Y])
		self.crossentropy = true_label_activation.mean()

def test_bilinear():
	num_features = 50
	n_out = 3
	num = 2000
	x1 = np.random.randn(num, num_features)
	x2 = np.random.randn(num, num_features)

	s = np.random.randn(num, n_out)
	y = s.argmax(1)

	rng = np.random.RandomState(12)

	blm = BilinearLayer(rng, num_features, num_features, n_out, activation_fn=T.tanh)
	trainer = AdagradTrainer(blm, blm.hinge_loss, 0.01, 0.01)
	trainer.train([x1,x2,y], 10)


def test_linear_layers(num_features1, num_feature2, n_out, num):

	#x1 = sp.sparse.rand(num, num_features1).todense()
	x1 = np.random.randn(num, num_features1)
	w1 = np.random.randn(num_features1, n_out)
	s1 = x1.dot(w1)

	#x2 = sp.sparse.rand(num, num_features2).todense()
	x2 = np.random.randn(num, num_features2)
	w2 = np.random.randn(num_features2, n_out)
	s2 = x2.dot(w2)

	y = (s1 + s2).argmax(1)

	train = [x1[0:num/2,:], x2[0:num/2,:], y[0:num/2]]
	dev = [x1[num/2:,:], x2[num/2:,:], y[num/2:]]

	rng = np.random.RandomState(12)

	lm = LinearLayer(rng, [num_features1, num_features2], n_out, False,
			Y=T.lvector(), activation_fn=None)
	print 'Training with hinge loss'
	trainer = AdagradTrainer(lm, lm.hinge_loss, 0.01, 0.01)
	start_time = timeit.default_timer()
	trainer.train_minibatch(100, 20, train, dev, dev)
	end_time = timeit.default_timer()
	print end_time - start_time 
	
def test_sparse_linear_layers(num_features1, num_features2, n_out, num):

	x1 = sp.sparse.rand(num, num_features1).tocsr()
	w1 = np.random.randn(num_features1, n_out)
	s1 = x1.dot(w1)

	x2 = sp.sparse.rand(num, num_features2).tocsr()
	w2 = np.random.randn(num_features2, n_out)
	s2 = x2.dot(w2)

	y = (s1 + s2).argmax(1)

	train = [x1[0:num/2,:], x2[0:num/2,:], y[0:num/2]]
	dev = [x1[num/2:,:], x2[num/2:,:], y[num/2:]]

	from learning import AdagradTrainer
	rng = np.random.RandomState(12)

	X1 = theano.sparse.csr_matrix('x1')
	X2 = theano.sparse.csr_matrix('x2')

	lm = LinearLayer(rng, [num_features1, num_features2], n_out, True, X_list=[X1, X2],
			Y=T.lvector(), activation_fn=None)
	print 'Training with hinge loss'
	trainer = AdagradTrainer(lm, lm.hinge_loss, 0.01, 0.01)
	start_time = timeit.default_timer()
	trainer.train_minibatch(100, 20, train, dev, dev)
	end_time = timeit.default_timer()
	print end_time - start_time 


if __name__ == '__main__':
	num_features1 = 4000
	num_features2 = 2000
	n_out = 3
	num = 10000
	test_sparse_linear_layers(num_features1, num_features2, n_out, num)
	test_linear_layers(num_features1, num_features2, n_out, num)
