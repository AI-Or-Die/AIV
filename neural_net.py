import tensorflow as tf
import numpy as np

class NeuralNet():

    def generate(self, layers):
        self.layers = layers
        self.activation = lambda x : tf.maximum(0.01*x, x)
        self.session = tf.Session()
        self.input_layer = tf.placeholder("float", [None, self.layers[0]],name="input")
        self.hidden_layer = []
        self.ff_weights = []
        self.ff_bias = []

        for i in range(len(self.layers[:-1])):
            self.ff_weights.append(tf.Variable(tf.truncated_normal([self.layers[i],self.layers[i+1]], mean=0.0, stddev=0.1)))
            self.ff_bias.append(tf.Variable(tf.constant(-0.01, shape = [self.layers[i+1]])))
            if i==0:
                activation = self.input_layer
            else:
                activation = self.activation(tf.matmul(self.hidden_layer[i-1],self.ff_weights[i-1])+self.ff_bias[i-1])
            self.hidden_layer.append(activation)

        self.state_value_layer = tf.add(tf.matmul(self.hidden_layer[-1], self.ff_weights[-1]), self.ff_bias[-1], name="state_value_layer")
        self.actions = tf.placeholder("float", [None,self.layers[-1]],name="actions")
        self.target = tf.placeholder("float", [None],name="target")
        self.action_value_vector = tf.reduce_sum(tf.multiply(self.state_value_layer,self.actions),1)
        self.cost = tf.reduce_sum(tf.square(self.target - self.action_value_vector))
        self.optimizer = tf.train.AdamOptimizer(1e-3).minimize(self.cost)

        self.session.run(tf.global_variables_initializer())
        self.feed_forward = lambda state: self.session.run(self.state_value_layer, feed_dict={self.input_layer: state})
        self.back_prop = lambda states, actions, target: self.session.run(
            self.optimizer,
            feed_dict={
                self.input_layer: states,
                self.actions: actions,
                self.target: target
            })


    def fit(self, states, actions, target):
        self.back_prop(states, actions, target)

    def predict(self, state):
        return self.feed_forward(state)

    def export(export_dir):
        variables = {}
        for i in range(len(self.layers[:-1])):
            variables["weights-{}".format(i)]=self.ff_weights[i]
            variables["bias-{}".format(i)]=self.ff_bias[i]
        saver = tf.train.Saver(variables)
        saver.save(self.session, export_dir, global_step=0)

    def restore(self):
        self.session = tf.Session()
        new_saver = tf.train.import_meta_graph('trained_models/aiv_logic-0.meta')
        new_saver.restore(self.session, 'trained_models/aiv_logic-0')
        self.input_layer = self.session.graph.get_tensor_by_name("input:0")
        self.state_value_layer = self.session.graph.get_tensor_by_name("state_value_layer:0")
        self.feed_forward = lambda state: self.session.run(self.state_value_layer, feed_dict={self.input_layer: state})

nn = NeuralNet()
nn.restore()

def pick_action(action):
    s = 0
    a = 0
    if action==0:
        a = -1
    elif action==1:
        a = 1
    elif action==2:
        self.aiv.move(1.0)
        s = 1.0
    elif action==3:
        s = 0.5
    elif action==4:
        s = 0
    return [a,s]

def to_ascii(direction: int, angle: int=None, speed: float=0.0):
    """Generate control sequence"""

    if angle is not None and angle:
        result = 'AK'[::-angle]
    elif speed == 0.5:
        result = 'KK'
    elif speed == 1.0:
        result = 'UU'
    else:
        result = 'AA'

    return result if direction == 1 else result.lower()

def predict(heading,distance,direction):
    a = np.argmax(nn.predict(observation.reshape(1, len(observation))))
    a = pick_action(a)
    return to_ascii(direction=direction,angle=a[0],speed=a[1])
