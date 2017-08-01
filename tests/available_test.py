# Test for is_available()

from tcpb import TCProtobufClient

from mock_server import MockServer

# JOB OUTPUT
expected_cycles = 4

# RUN TEST
def run_test(port=56789, run_real_server=False):
    """Run the test

    Args:
        port: Port to use for server and client in testing
        run_real_server: If True, we expect a real TCPB server and record a packet trace
                         If False, run the test with MockServer and the recorded packet trace
    Returns True if passed the tests, and False if failed the tests
    """
    # Set up MockServer for testing
    if not run_real_server:
        mock = MockServer(port, 'available/client_recv.bin', 'available/client_sent.bin')

    with TCProtobufClient(host='localhost', port=port, trace=run_real_server, method='hf', basis='sto-3g') as TC:
        count = 0
        while not TC.is_available():
            count += 1

        if count != expected_cycles:
            print('Expected {} cycles, but only got {}'.format(expected_cycles, count))
            return False

    return True

if __name__ == '__main__':
    run_test()
    #run_test(run_real_server=True)

