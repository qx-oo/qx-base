class SendMobileMsgMixin():

    def send_verify_code(self, mobile, code):
        """
        Send Verify Code
        """
        raise NotImplementedError()


class SendEmailMsgMixin():

    def send_verify_code(self, email, code):
        """
        Send Verify Code
        """
        raise NotImplementedError()
