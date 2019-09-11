from .base import ModelPolicy
from sklearn.linear_model import LogisticRegression
import functools
import pickle
import os


class LRPolicy(ModelPolicy):
    def __init__(self, name, atype, model, strategy):
        super().__init__(name, atype, model, strategy)

    def init_model(self, model, classmap):
        if isinstance(model, LogisticRegression):
            self.model = model
        elif isinstance(model, str):
            assert os.path.exists(model)
            with open(model, "rb") as f:
                self.model = pickle.load(f)
            assert isinstance(self.model, LogisticRegression)
        else:
            raise Exception("Unknown model for LRPolicy")

        self.classmap = {cls: i for i, cls in enumerate(self.model.classes_)}  # class name (str) to index (int)
