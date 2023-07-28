import time


# =========================================================================
# PerformanceTimer
# =========================================================================
class PerformanceTimer:
    name = ""
    start_t = -1
    end_t = -1
    duration_t = 0

    def __init__(self, name):
        self.name = name

    def start(self):
        self.start_t = time.perf_counter()

    def stop(self):
        if self.start_t != -1:
            self.end_t = time.perf_counter()
            self.duration_t = self.end_t - self.start_t
            self.start_t = -1

    def duration(self, stop=False):
        if self.start_t != -1:
            self.end_t = time.perf_counter()
            self.duration_t = self.end_t - self.start_t
            if stop:
                self.start_t = -1

        return self.duration_t

    def print_duration(self, stop=False):
        print(f"{self.name} duration: {self.duration(stop):.4f}s")

