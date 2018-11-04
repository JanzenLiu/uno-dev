from .base import ModelPolicy
import keras as ks
import os


class KerasPolicy(ModelPolicy):
    def __init__(self, name, atype, model, strategy, classmap):
        super().__init__(name, atype, model, strategy, classmap)

    def init_model(self, model, classmap):
        if isinstance(model, ks.models.Model):
            self.model = model
        elif isinstance(model, str):
            assert os.path.exists(model)
            self.model = ks.models.load_model(model)
            assert isinstance(self.model, ks.models.Model)
        else:
            raise Exception("Unknown model for LRPolicy")

        self.classmap = classmap  # class name (str) to index (int)
