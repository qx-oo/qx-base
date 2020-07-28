class SendMobileMsgMixin():

    def send_msg(self, mobile, msg):
        raise NotImplementedError()


class SendEmailMsgMixin():

    def send_msg(self, email, msg):
        raise NotImplementedError()
