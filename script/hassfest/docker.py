"""Generate and validate the dockerfile."""

from homeassistant import core
from homeassistant.util import executor, thread

from .model import Config, Integration
from .requirements import PACKAGE_REGEX, PIP_VERSION_RANGE_SEPARATOR

DOCKERFILE_TEMPLATE = r"""# Automatically generated by hassfest.
#
# To update, run python3 -m script.hassfest -p docker
ARG BUILD_FROM
FROM ${{BUILD_FROM}}

# Synchronize with homeassistant/core.py:async_stop
ENV \
    S6_SERVICES_GRACETIME={timeout} \
    UV_SYSTEM_PYTHON=true

ARG QEMU_CPU

# Install uv
RUN pip3 install uv=={uv_version}

WORKDIR /usr/src

## Setup Home Assistant Core dependencies
COPY requirements.txt homeassistant/
COPY homeassistant/package_constraints.txt homeassistant/homeassistant/
RUN \
    uv pip install \
        --no-build \
        -r homeassistant/requirements.txt

COPY requirements_all.txt home_assistant_frontend-* home_assistant_intents-* homeassistant/
RUN \
    if ls homeassistant/home_assistant_*.whl 1> /dev/null 2>&1; then \
        uv pip install homeassistant/home_assistant_*.whl; \
    fi \
    && if [ "${{BUILD_ARCH}}" = "i386" ]; then \
        LD_PRELOAD="/usr/local/lib/libjemalloc.so.2" \
        MALLOC_CONF="background_thread:true,metadata_thp:auto,dirty_decay_ms:20000,muzzy_decay_ms:20000" \
        linux32 uv pip install \
            --no-build \
            -r homeassistant/requirements_all.txt; \
    else \
        LD_PRELOAD="/usr/local/lib/libjemalloc.so.2" \
        MALLOC_CONF="background_thread:true,metadata_thp:auto,dirty_decay_ms:20000,muzzy_decay_ms:20000" \
        uv pip install \
            --no-build \
            -r homeassistant/requirements_all.txt; \
    fi

## Setup Home Assistant Core
COPY . homeassistant/
RUN \
    uv pip install \
        -e ./homeassistant \
    && python3 -m compileall -j 4 \
        homeassistant/homeassistant

# Home Assistant S6-Overlay
COPY rootfs /

WORKDIR /config
"""


def _get_uv_version() -> str:
    with open("requirements_test.txt") as fp:
        for _, line in enumerate(fp):
            if match := PACKAGE_REGEX.match(line):
                pkg, sep, version = match.groups()

                if pkg != "uv":
                    continue

                if sep != "==" or not version:
                    raise RuntimeError(
                        'Requirement uv need to be pinned "uv==<version>".'
                    )

                for part in version.split(";", 1)[0].split(","):
                    version_part = PIP_VERSION_RANGE_SEPARATOR.match(part)
                    if version_part:
                        return version_part.group(2)

    raise RuntimeError("Invalid uv requirement in requirements_test.txt")


def _generate_dockerfile() -> str:
    timeout = (
        core.STOPPING_STAGE_SHUTDOWN_TIMEOUT
        + core.STOP_STAGE_SHUTDOWN_TIMEOUT
        + core.FINAL_WRITE_STAGE_SHUTDOWN_TIMEOUT
        + core.CLOSE_STAGE_SHUTDOWN_TIMEOUT
        + executor.EXECUTOR_SHUTDOWN_TIMEOUT
        + thread.THREADING_SHUTDOWN_TIMEOUT
        + 10
    )
    return DOCKERFILE_TEMPLATE.format(
        timeout=timeout * 1000, uv_version=_get_uv_version()
    )


def validate(integrations: dict[str, Integration], config: Config) -> None:
    """Validate dockerfile."""
    dockerfile_content = _generate_dockerfile()
    config.cache["dockerfile"] = dockerfile_content

    dockerfile_path = config.root / "Dockerfile"
    if dockerfile_path.read_text() != dockerfile_content:
        config.add_error(
            "docker",
            "File Dockerfile is not up to date. Run python3 -m script.hassfest",
            fixable=True,
        )


def generate(integrations: dict[str, Integration], config: Config) -> None:
    """Generate dockerfile."""
    dockerfile_path = config.root / "Dockerfile"
    dockerfile_path.write_text(config.cache["dockerfile"])
