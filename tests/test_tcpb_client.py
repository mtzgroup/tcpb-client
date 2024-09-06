from qcio import ProgramOutput

from tcpb.clients import TCProtobufClient
from tcpb.exceptions import ServerError


def test_compute_failed_operation(mocker, prog_input):
    client = TCProtobufClient()
    # Cause _send_msg to raise ServerError
    patch = mocker.patch("tcpb.clients.TCProtobufClient._send_msg")
    patch.side_effect = ServerError("my message", client)
    # Try computation
    prog_output = client.compute(prog_input)
    assert isinstance(prog_output, ProgramOutput)
    assert prog_output.success is False
