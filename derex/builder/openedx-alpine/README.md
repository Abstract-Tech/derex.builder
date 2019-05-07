Alpine docker image
===================

This directory contains scripts to build an openedx image based
on Alpine Linux. The goal is to have a small image and fast image build.

Images used in intermediate steps
---------------------------------

To achieve the goal of fast image build, image preparation is divided into multiple steps.

The idea behind this is that some parts change more often than others, and we can build base images with the ones that are seldom updated, like operating system dependencies; the same reasoning is done about python wheels and the edx-platform code itself.

Two images are created using the python alpine one as a base.
One includes all packages needed to build wheels, the other one with packages needed at runtime.

The wheels builder is used to build the wheels, and they are pip installed into the runtime image.

At this point the runtime image is able to run code provided by an `edx-platform` checkout and config files.

The last image bundles edx-platform.

These are the image names:

* `openedx-alpine-buildwheels`: build dependencies included
* `openedx-alpine-base`: just runtime dependencies
* `openedx-alpine-wheels`: wheels preinstalled for a specific edx-platform version, but no python code from edx-platform
* `openedx-alpine`: edx-platform code included
