class SendException(Exception):

    def __init__(self, description, url, method, request, response, response_status, fatal=False):
        super(SendException, self).__init__(description)

        self.description = description
        self.url = url
        self.method = method
        self.request = request
        self.response = response
        self.response_status = response_status
        self.fatal = fatal