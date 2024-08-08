from reliability.Distributions import Weibull_Distribution, Lognormal_Distribution, Exponential_Distribution
import numpy as np
import random
from typing import List

class Reliability:
    def __init__(self, maxValue: int, count_of_total_nodes: int):
        self.xvals = np.linspace(0, maxValue, count_of_total_nodes)
        self.infant_mortality = None
        self.random_failures = None
        self.wear_out = None
        self.bathtub_curve = None
        self.count_of_total_nodes: int = count_of_total_nodes
        self.count_of_normal_nodes: int = 0
        self.count_of_faulty_nodes: int = 0
        self.list_of_random_failures: List[int] = []
        
    def generate_infant_mortality(self, alpha, beta):
        self.infant_mortality = Weibull_Distribution(alpha, beta).HF(xvals=self.xvals, show_plot=False)[1:]
        
    def generate_random_failures(self, Lambda):
        self.random_failures = Exponential_Distribution(Lambda).HF(xvals=self.xvals, show_plot=False)
    
    def generate_wear_out(self, mu, sigma):
        self.wear_out = Lognormal_Distribution(mu, sigma).HF(xvals=self.xvals, show_plot=False)

    def generate_bathtub_curve(self):    
        self.bathtub_curve = self.infant_mortality + self.random_failures + self.wear_out
        
    def random_choice(self, weights: List[float]) -> int:
        return random.choices([0, 1], weights=weights)[0]
    
    def get_weights(self, failure_rate: float) -> List[float]:
        scaled_failure_rate = min(failure_rate * 100, 1)
        success_rate = 1 - scaled_failure_rate
        return [success_rate, scaled_failure_rate]
    
    def get_random_failures(self, model):
        for i in range(0, len(model)):
            weights = self.get_weights(model[i])
            self.list_of_random_failures.append(self.random_choice(weights))
        
        self.count_faulty_nodes()
        
    def count_faulty_nodes(self):
        for i in range(0, len(self.list_of_random_failures)):
            if self.list_of_random_failures[i] == 1:
                self.count_of_faulty_nodes += 1
            else:
                self.count_of_normal_nodes += 1

