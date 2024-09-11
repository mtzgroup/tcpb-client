from tcpb import TCFrontEndClient


def test_pre_compute_tasks_does_not_put_files_if_none_passed(prog_input, mocker):
    spy = mocker.patch("tcpb.TCFrontEndClient.put")

    client = TCFrontEndClient()
    client._pre_compute_tasks(prog_input)

    spy.assert_not_called()


def test_pre_compute_tasks_upload_c0(prog_input, mocker):
    filename = "c0"
    filedata = b"123"

    prog_input.files[filename] = filedata

    spy = mocker.patch("tcpb.TCFrontEndClient.put")

    client = TCFrontEndClient()
    client._pre_compute_tasks(prog_input)

    spy.assert_called_once_with(filename, filedata)


def test_pre_compute_tasks_upload_ca0_cb0(prog_input, mocker):
    filename_a = "ca0"
    filedata_a = b"123"

    filename_b = "cb0"
    filedata_b = b"xyz"

    prog_input.files[filename_a] = filedata_a
    prog_input.files[filename_b] = filedata_b

    spy = mocker.patch("tcpb.TCFrontEndClient.put")

    client = TCFrontEndClient()
    client._pre_compute_tasks(prog_input)

    assert spy.call_count == 2
    spy.assert_any_call(filename_a, filedata_a)
    spy.assert_any_call(filename_b, filedata_b)


def test_post_compute_tasks_removes_job_dir_by_default(prog_output, mocker):
    """Implies scratch_messy and uploads_messy missing. Should cleanup directory after job"""

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(prog_output, collect_stdout=False, collect_files=False)

    spy.assert_called_once_with("DELETE", f"{prog_output.provenance.scratch_dir}/")


def test_post_compute_tasks_retains_job_dir_is_scratch_messy(prog_output, mocker):
    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(prog_output, collect_stdout=False, rm_scratch_dir=False, collect_files=False)

    spy.assert_not_called()


def test_post_compute_tasks_guess_not_removed_if_not_in_uploads_dir(
    prog_output, mocker
):
    """This tests that if a user is 'manually' passing a path to a previously computed c0
    file it does not get cleaned up by default. Only files in the uploads_dir (indicating
    that they were uploaded by the client) will get cleaned up
    """

    # Set guess value NOT from a client upload (no client.uploads_prefix in path)
    client = TCFrontEndClient()
    prog_output.input_data.keywords["guess"] = "path/to/c0"

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(prog_output, collect_stdout=False, rm_scratch_dir=False, collect_files=False)

    spy.assert_not_called()


def test_post_compute_tasks_cleans_uploads_single_c0(prog_output, mocker):
    # Set guess value to trigger uploads cleaning
    client = TCFrontEndClient()
    path = f"{client.uploads_prefix}/path/to/c0"
    prog_output.input_data.keywords["guess"] = path

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(prog_output, collect_stdout=False, collect_files=False)

    spy.assert_any_call("DELETE", path)


def test_post_compute_tasks_cleans_uploads_ca0_cb0(prog_output, mocker):
    # Set guess value to trigger uploads cleaning
    client = TCFrontEndClient()
    patha = f"{client.uploads_prefix}/path/to/ca0"
    pathb = f"{client.uploads_prefix}/path/to/cb0"
    path = f"{patha} {pathb}"
    prog_output.input_data.keywords["guess"] = path

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(prog_output, collect_stdout=False, collect_files=False)

    assert spy.call_count == 3  # once for the whole scratch dir, once for each file
    spy.assert_any_call("DELETE", patha)
    spy.assert_any_call("DELETE", pathb)


def test_post_compute_tasks_retrieves_stdout(prog_output, mocker):
    """stdout should be retrieved by default"""

    stdout = b"my fake stdout"

    class fakerequest:
        text = stdout

    spy = mocker.patch("tcpb.TCFrontEndClient.get")
    spy.return_value = stdout

    client = TCFrontEndClient()
    post_compute_result = client._post_compute_tasks(prog_output, collect_files=False, rm_scratch_dir=False)

    spy.assert_called_with(f"{prog_output.provenance.scratch_dir}/tc.out")

    assert post_compute_result.stdout == stdout.decode()


def test_post_compute_tasks_retrieves_stdout_failed_operation(prog_output, mocker):
    """stdout retrieved by default on failures"""
    stdout = b"my fake stdout"
    failed_prog_output = prog_output.model_copy(
        update={"success": False, "stdout": stdout, "traceback": "fake traceback"}
    )

    class fakerequest:
        text = stdout

    spy = mocker.patch("tcpb.TCFrontEndClient.get")
    spy.return_value = stdout

    client = TCFrontEndClient()
    post_compute_result = client._post_compute_tasks(
        failed_prog_output, rm_scratch_dir=False, collect_stdout=False, collect_files=False
    )
    spy.assert_called_with("/tmp/tc.out")

    assert post_compute_result.stdout == stdout.decode()


def test_post_compute_tasks_does_not_retrieve_stdout_or_native_files(
    prog_output, mocker
):
    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(
        prog_output, collect_stdout=False, collect_files=False, rm_scratch_dir=False
    )

    spy.assert_not_called()


def test_collect_files_queries_for_all_files_if_none_specified(prog_output, mocker):
    spy = mocker.patch("tcpb.TCFrontEndClient.ls")

    client = TCFrontEndClient()
    client._collect_files(prog_output)

    # Filter out any __iter__ calls
    filtered_calls = [call for call in spy.mock_calls if call[0] == ""]

    # Assert that both "/tmp" and "/tmp/scr" were called
    assert mocker.call("/tmp") in filtered_calls
    assert mocker.call("/tmp/scr") in filtered_calls
