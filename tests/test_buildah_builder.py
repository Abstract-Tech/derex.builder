#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""builder"""

from .utils import get_builder_path
from derex.builder.builders.buildah import BuildahBuilder
from jsonschema.exceptions import ValidationError
from pathlib import PosixPath
from pytest_mock import MockFixture

import docker
import logging
import os
import pytest


logger = logging.getLogger()


@pytest.mark.slowtest
@pytest.mark.buildah
def test_buildah_builder_base(buildah_base: BuildahBuilder):
    os.environ["BUILD_VAR"] = "the build variable"
    buildah_base.build()
    buildah_base.push_to_docker()

    # Check the generated docker image
    client = docker.from_env()
    response = client.containers.run(buildah_base.dest, "cat /hello.txt", remove=True)
    assert response == b"Greetings!\nHello world!\n"
    response = client.containers.run(buildah_base.dest, "pwd", remove=True)
    assert response == b"Greetings!\n/usr/share/apk/keys\n"

    # Make sure environment variables were properly set during build
    response = client.containers.run(
        buildah_base.dest, "cat /build_var.txt", remove=True
    )
    assert response == b"Greetings!\nthe build variable\n"

    response = client.containers.run(
        buildah_base.dest, 'sh -c "echo $FOO"', remove=True
    )
    assert response == b"Greetings!\nbar\n"
    client.images.remove(buildah_base.dest)

    images = BuildahBuilder.list_buildah_images()
    assert f"{buildah_base.source.replace('docker.io/', '')}" in images


def test_hash_conf(buildah_base: BuildahBuilder):
    initial = buildah_base.hash_conf()
    buildah_base.conf["foo"] = "bar"
    assert buildah_base.hash_conf() != initial


def test_hash(buildah_base: BuildahBuilder, tmp_path: PosixPath):
    tmp_file = tmp_path / "script.sh"
    tmp_file.write_text("foo")
    buildah_base.scripts = [tmp_file.as_posix()]
    initial = buildah_base.hash()
    tmp_file.write_text("bar")
    assert buildah_base.hash() != initial


def test_caches(buildah_base: BuildahBuilder, tmp_path: PosixPath):
    os.environ["PIP_CACHE"] = f"{tmp_path}/pip-alpine"
    buildah_base.ensure_caches()
    assert os.path.exists(os.environ["PIP_CACHE"])


@pytest.mark.slowtest
@pytest.mark.buildah
def test_resolve(buildah_base: BuildahBuilder, mocker: MockFixture):
    list_buildah_images = mocker.patch(
        "derex.builder.builders.buildah.BuildahBuilder.list_buildah_images"
    )
    list_buildah_images.return_value = []  # When the image is not available locally...
    build = mocker.patch("derex.builder.builders.buildah.BuildahBuilder.build")
    buildah_base.resolve()
    build.assert_called_once()  # ...it will be built

    # If the image is present locally it will not be built
    list_buildah_images.return_value = [f"localhost/{buildah_base.dest}"]
    buildah_base.resolve()
    build.reset_mock()
    build.assert_not_called()


def test_error_call():
    with pytest.raises(RuntimeError):
        BuildahBuilder.buildah("foobar")


def test_create_builder(buildah_base):
    from derex.builder.builders.base import create_builder, ConfigurationError

    buildah_base_spec = get_builder_path("base")
    base = create_builder(buildah_base_spec + "/")
    assert base.hash() == buildah_base.hash()
    assert type(base) == type(buildah_base)

    buildah_invalid_spec = get_builder_path("invalid")
    with pytest.raises(ValidationError):
        create_builder(buildah_invalid_spec)


@pytest.mark.slowtest
@pytest.mark.buildah
def test_dependent_container(buildah_base: BuildahBuilder):
    assert buildah_base.dest not in BuildahBuilder.list_buildah_images()

    # Make sure a trailing slash doesn't spoil the party
    buildah_dependent_spec = get_builder_path("dependent") + "/"
    buildah_dependent = BuildahBuilder(buildah_dependent_spec)

    buildah_dependent.build()
    container = BuildahBuilder.buildah("from", buildah_dependent.dest)
    response = BuildahBuilder.buildah("run", container, "cat", "/hello_all.txt")
    assert response == "Hello all!"
    BuildahBuilder.buildah("rm", container)
    # Make sure the dependent image was also committed and tagged
    assert buildah_base.dest in BuildahBuilder.list_buildah_images()


def test_sudo_only_if_necessary(mocker: MockFixture):
    run = mocker.patch("derex.builder.builders.base.BaseBuilder.run")
    getuid = mocker.patch("derex.builder.builders.buildah.os.getuid")
    getuid.return_value = 1000
    BuildahBuilder.buildah()
    assert run.call_args[0][0] == ["sudo", "buildah"]
    getuid.return_value = 0
    BuildahBuilder.buildah()
    assert run.call_args[0][0] == ["buildah"]


@pytest.fixture
def buildah_base() -> BuildahBuilder:
    buildah_base_spec = get_builder_path("base")
    return BuildahBuilder(buildah_base_spec)


@pytest.fixture(autouse=True)
def clean_up_images() -> None:
    # Remove all containers derived from derextests images
    for container in BuildahBuilder.buildah("ls").split("\n")[1:]:
        container_info = container.split()
        if len(container_info) != 5:
            continue
        container_id, _, _, image_name, container_name = container_info
        if image_name.startswith("localhost/derextests"):
            BuildahBuilder.buildah("rm", container_id)
            logger.warn(f"Removed container {container_name}")

    for image in BuildahBuilder.list_buildah_images():
        if image.startswith("derextests"):
            BuildahBuilder.buildah("rmi", image)
            logger.warn(f"Removed image {image}")


def test_check_docker_registry(buildah_base: BuildahBuilder, mocker: MockFixture):
    urlopen = mocker.patch("derex.builder.builders.base.urllib.request.urlopen")
    response = mocker.Mock()
    response.read.return_value = (
        f'{{"token": "", "tags": ["{buildah_base.docker_tag()}"]}}'
    )

    urlopen.return_value = response

    assert buildah_base.available_docker_registry()
