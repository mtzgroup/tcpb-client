# Contributing

## Developing

If you already cloned the repository and you know that you need to deep dive in the code, here are some guidelines to set up your environment.

Note that lots of apparently unused code was removed from the repo to clean it up and make clear the actual code under development. To review all old code previously in the repo checkout the `r0.6.0` tag.

### Virtual environment with `venv`

You can create a virtual environment in a directory using Python's `venv` module:

```console
$ python -m venv env
```

That will create a directory `./env/` with the Python binaries and then you will be able to install packages for that isolated environment.

### Activate the environment

Activate the new environment with:

```console
$ source ./env/bin/activate
```

To check it worked, use:

```console
$ which pip
some/directory/tcpb/env/bin/pip
```

If it shows the `pip` binary at `env/bin/pip` then it worked. 🎉

‼️ tip
Every time you install a new package with `pip` under that environment, activate the environment again.

This makes sure that if you use a terminal program installed by that package (like `flit`), you use the one from your local environment and not any other that could be installed globally.

### Flit

**tcpb** uses <a href="https://flit.readthedocs.io/en/latest/index.html" class="external-link" target="_blank">Flit</a> to build, package and publish the project.

After activating the environment as described above, install `flit`:

```console
$ pip install flit

---> 100%
```

Now re-activate the environment to make sure you are using the `flit` you just installed (and not a global one).

And now use `flit` to install the development dependencies:

```console
$ flit install --deps develop --symlink
---> 100%
```

It will install all the dependencies and your local tcpb in your local environment.

#### Using your local tcpb

If you create a Python file that imports and uses tcpb, and run it with the Python from your local environment, it will use your local tcpb source code.

And if you update that local tcpb source code, as it is installed with `--symlink` (or `--pth-file` on Windows), when you run that Python file again, it will use the fresh version of tcpb you just edited.

That way, you don't have to "install" your local version to be able to test every change.

## Tests

Use `pytest` to test all the code.

```console
pytest
```

This command requires a TeraChem server running on the host and server set in `tests/conftest.py`, `localhost` and port `11111` by default. Often running a TeraChem server on Fire and using port forwarding is the easiest way to accomplish this. Tests in the `tests/test_utils.py` file do not require a TeraChem server.
