from __future__ import absolute_import, division, print_function

"""Exception handling for tcpb package

See https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions
"""


class TCPBError(Exception):
    """Base error for package"""


class ServerError(TCPBError):
    """Raised when socket connection to server dies

    Pulls logfile out of scratch dir for convenience
    """

    def __init__(self, msg, client):
        msg += "\n\nServer Address: {}\n".format((client.host, client.port))

        job_dir = client.curr_job_dir
        job_id = client.curr_job_id
        try:
            logfile = "{}/{}.log".format(job_dir, job_id)
            with open(logfile, "r") as logf:
                lines = logf.readlines()

            debuglines = "".join(lines[-10:])
            msg += "Last 10 lines from logfile ({}):\n{}".format(logfile, debuglines)
        except IOError:
            msg += "Could not open logfile"

        super(ServerError, self).__init__(msg)
