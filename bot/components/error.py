class Error:
    def msg(e, f=""):
        template = "An exception of type {0} occurred" + \
            f + ". Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print("An exception!... {}".format(message))
