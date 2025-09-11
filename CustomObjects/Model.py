import concurrent.futures
from CustomObjects.Dataset import Dataset
from CustomObjects.Code import Code

class Model:
    def __init__(self, model_url, dataset_url, code_url):
        self.url = model_url
        self.size = 0
        self.license = ""
        self.ramp_up_time = 0
        self.bus_factor = 0
        self.dataset = Dataset(dataset_url) #Contains dataset quality and availability scores
        self.code = Code(code_url) #Contains code quality and availability scores
        self.performance_claims = 0
        self.net_score = 0

    def get_size(self):
        #TODO implement size assessment logic
        return 1
    
    def get_license(self):
        #TODO implement license assessment logic
        return 1
    
    def get_ramp_up_time(self):
        #TODO implement ramp up time assessment logic
        return 1
    
    def get_bus_factor(self):
        #TODO implement bus factor assessment logic
        return 1
    
    def get_performance_claims(self):
        #TODO implement performance claims assessment logic
        return 1
    
    def compute_net_score(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_size = executor.submit(self.get_size)
            future_license = executor.submit(self.get_license)
            future_ramp_up_time = executor.submit(self.get_ramp_up_time)
            future_bus_factor = executor.submit(self.get_bus_factor)
            future_dataset_quality = executor.submit(self.dataset.get_quality)
            future_code_quality = executor.submit(self.code.get_quality)
            future_performance_claims = executor.submit(self.get_performance_claims)

            self.size = future_size.result()
            self.license = future_license.result()
            self.ramp_up_time = future_ramp_up_time.result()
            self.bus_factor = future_bus_factor.result()
            self.dataset.quality = future_dataset_quality.result()
            self.code.quality = future_code_quality.result()
            self.performance_claims = future_performance_claims.result()

        # Example weights, can be adjusted based on importance
        weights = {
            'license': 0.25,
            'ramp_up_time': 0.05,
            'bus_factor': 0.15,
            'dataset_quality': 0.195,
            'dataset_availability': 0.025,
            'code_quality': 0.005,
            'code_availability': 0.025,
            'performance_claims': 0.30
        }

        self.net_score = (
            weights['license'] * self.license +
            weights['ramp_up_time'] * self.ramp_up_time +
            weights['bus_factor'] * self.bus_factor +
            weights['dataset_quality'] * self.dataset.quality +
            weights['dataset_availability'] * self.dataset.dataset_availability +
            weights['code_quality'] * self.code.quality +
            weights['code_availability'] * self.code.code_availability +
            weights['performance_claims'] * self.performance_claims
        )

        return self.net_score