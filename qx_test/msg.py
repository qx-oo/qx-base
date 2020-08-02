from qx_base.qx_user.mixins import SendEmailMsgMixin, SendMobileMsgMixin


class TestMsg(SendEmailMsgMixin, SendMobileMsgMixin):

    def send_msg(self, send_name, msg):
        print("{} send {}".format(send_name, msg))
