from qcelemental.models import AtomicResult

from tcpb import TCFrontEndClient
from tcpb.config import settings


def test_pre_compute_tasks_does_not_put_files_if_none_passed(atomic_input, mocker):
    spy = mocker.patch("tcpb.TCFrontEndClient.put")

    client = TCFrontEndClient()
    client._pre_compute_tasks(atomic_input)

    spy.assert_not_called()


def test_pre_compute_tasks_upload_c0(atomic_input, mocker):
    filename = "c0"
    filedata = b"123"

    atomic_input.extras[settings.tcfe_keywords] = {filename: filedata}

    spy = mocker.patch("tcpb.TCFrontEndClient.put")

    client = TCFrontEndClient()
    client._pre_compute_tasks(atomic_input)

    spy.assert_called_once_with(filename, filedata)


def test_pre_compute_tasks_upload_ca0_cb0(atomic_input, mocker):
    filename_a = "ca0"
    filedata_a = b"123"

    filename_b = "cb0"
    filedata_b = b"xyz"

    atomic_input.extras[settings.tcfe_keywords] = {
        filename_a: filedata_a,
        filename_b: filedata_b,
    }

    spy = mocker.patch("tcpb.TCFrontEndClient.put")

    client = TCFrontEndClient()
    client._pre_compute_tasks(atomic_input)

    assert spy.call_count == 2
    spy.assert_any_call(filename_a, filedata_a)
    spy.assert_any_call(filename_b, filedata_b)


def test_post_compute_tasks_removes_job_dir_by_default(atomic_result, mocker):
    """Implies scratch_messy and uploads_messy missing. Should cleanup directory after job"""

    # Set stdout False so tc.out not retrieved
    modified_result = atomic_result.dict()
    modified_result["protocols"]["stdout"] = False

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(AtomicResult(**modified_result))

    spy.assert_called_once_with(
        "DELETE", f"{modified_result['extras'][settings.extras_job_kwarg]['job_dir']}/"
    )


def test_post_compute_tasks_retains_job_dir_is_scratch_messy(atomic_result, mocker):
    # Set stdout False so tc.out not retrieved
    modified_result = atomic_result.dict()
    modified_result["protocols"]["stdout"] = False
    modified_result["extras"][settings.tcfe_keywords] = {"scratch_messy": True}

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(AtomicResult(**modified_result))

    spy.assert_not_called()


def test_post_compute_tasks_guess_not_removed_if_not_in_uploads_dir(
    atomic_result, mocker
):
    """This tests that if a user is 'manually' passing a path to a previously computed c0
    file it does not get cleaned up by default. Only files in the uploads_dir (indicating
    that they were uploaded by the client) will get cleaned up
    """
    # Set stdout False so tc.out not retrieved
    modified_result = atomic_result.dict()
    modified_result["protocols"]["stdout"] = False

    # Set Scratch messy so no calls for removing scratch directory
    modified_result["extras"][settings.tcfe_keywords] = {"scratch_messy": True}

    # Set guess value NOT from a client upload (no client.uploads_prefix in path)
    client = TCFrontEndClient()
    modified_result["keywords"] = {"guess": "path/to/c0"}

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(AtomicResult(**modified_result))

    spy.assert_not_called()


def test_post_compute_tasks_cleans_uploads_single_c0(atomic_result, mocker):
    # Set stdout False so tc.out not retrieved
    modified_result = atomic_result.dict()
    modified_result["protocols"]["stdout"] = False

    # Set Scratch messy so no calls for removing scratch directory
    modified_result["extras"][settings.tcfe_keywords] = {"scratch_messy": True}

    # Set guess value to trigger uploads cleaning
    client = TCFrontEndClient()
    path = f"{client.uploads_prefix}/path/to/c0"
    modified_result["keywords"] = {"guess": path}

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(AtomicResult(**modified_result))

    spy.assert_called_once_with("DELETE", path)


def test_post_compute_tasks_cleans_uploads_ca0_cb0(atomic_result, mocker):
    # Set stdout False so tc.out not retrieved
    modified_result = atomic_result.dict()
    modified_result["protocols"]["stdout"] = False

    # Set Scratch messy so no calls for removing scratch directory
    modified_result["extras"][settings.tcfe_keywords] = {"scratch_messy": True}

    # Set guess value to trigger uploads cleaning
    client = TCFrontEndClient()
    patha = f"{client.uploads_prefix}/path/to/ca0"
    pathb = f"{client.uploads_prefix}/path/to/cb0"
    path = f"{patha} {pathb}"
    modified_result["keywords"] = {"guess": path}

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(AtomicResult(**modified_result))

    assert spy.call_count == 2
    spy.assert_any_call("DELETE", patha)
    spy.assert_any_call("DELETE", pathb)


def test_post_compute_tasks_retrieves_stdout(atomic_result, mocker):
    """stdout set True be default on AtomicResultProtocols, should be retrieved by
    default"""

    # Set Scratch messy so no calls for removing scratch directory
    modified_result = atomic_result.dict()
    modified_result["extras"][settings.tcfe_keywords] = {"scratch_messy": True}

    stdout = b"my fake stdout"

    class fakerequest:
        text = stdout

    spy = mocker.patch("tcpb.TCFrontEndClient.get")
    spy.return_value = stdout

    client = TCFrontEndClient()
    post_compute_result = client._post_compute_tasks(AtomicResult(**modified_result))

    spy.assert_called_with(
        f"{modified_result['extras'][settings.extras_job_kwarg]['job_dir']}/tc.out",
    )

    assert post_compute_result.stdout == stdout.decode()


def test_post_compute_tasks_does_not_retrieve_stdout_or_native_files(
    atomic_result, mocker
):
    # Set Scratch messy so no calls for removing scratch directory
    modified_result = atomic_result.dict()
    modified_result["extras"][settings.tcfe_keywords] = {"scratch_messy": True}
    modified_result["protocols"]["stdout"] = False

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(AtomicResult(**modified_result))

    spy.assert_not_called()


def test_post_compute_tasks_no_files_collected_native_files(atomic_result, mocker):
    # Set Scratch messy so no calls for removing scratch directory
    modified_result = atomic_result.dict()
    modified_result["extras"][settings.tcfe_keywords] = {"scratch_messy": True}
    modified_result["protocols"]["stdout"] = False
    modified_result["protocols"]["native_files"] = "none"

    spy = mocker.patch("tcpb.TCFrontEndClient._request")

    client = TCFrontEndClient()
    client._post_compute_tasks(AtomicResult(**modified_result))

    spy.assert_not_called()


def test_collect_files_queries_for_all_files_if_none_specified(atomic_result, mocker):
    modified_result = atomic_result.dict()
    modified_result["extras"][settings.extras_job_kwarg]["job_scr_dir"] = "fake_scr_dir"
    print(modified_result["extras"][settings.extras_job_kwarg])

    spy = mocker.patch("tcpb.TCFrontEndClient.ls")

    client = TCFrontEndClient()
    client._collect_files(modified_result)

    spy.assert_called_once_with("fake_scr_dir")


def test_collect_files_only_collects_specified_files_if_passed(atomic_result, mocker):
    modified_result = atomic_result.dict()
    job_scr_dir = "fake_scr_dir"
    modified_result["extras"][settings.extras_job_kwarg]["job_scr_dir"] = job_scr_dir
    filenames = ["file1", "file2"]
    modified_result["extras"][settings.tcfe_keywords] = {"native_files": filenames}

    lsspy = mocker.patch("tcpb.TCFrontEndClient.ls")
    getspy = mocker.patch("tcpb.TCFrontEndClient.get")

    client = TCFrontEndClient()
    client._collect_files(modified_result)

    lsspy.assert_not_called()
    assert getspy.call_count == 2
    getspy.assert_any_call(f"{job_scr_dir}/{filenames[0]}")
    getspy.assert_any_call(f"{job_scr_dir}/{filenames[1]}")
