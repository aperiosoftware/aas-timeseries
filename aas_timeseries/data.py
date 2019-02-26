import uuid


class Data:

    def __init__(self, time_series):
        self.time_series = time_series
        self.uuid = str(uuid.uuid4())
        self.time_column = 'time'
