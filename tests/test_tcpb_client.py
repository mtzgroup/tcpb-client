from qcelemental.models import FailedOperation

from tcpb.clients import TCProtobufClient
from tcpb.exceptions import ServerError


def test_comptue_failed_operation(mocker, atomic_input):
    client = TCProtobufClient()
    # Cause _send_msg to raise ServerError
    patch = mocker.patch("tcpb.clients.TCProtobufClient._send_msg")
    patch.side_effect = ServerError("my message", client)
    # Try computation
    result = client.compute(atomic_input)
    assert isinstance(result, FailedOperation)
    assert result.error.error_type == "terachem_server_error"
