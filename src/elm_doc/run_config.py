import attr


@attr.s
class RunConfig:
    elm_path = attr.ib()  # Path
    build_path = attr.ib()  # Path


@attr.s
class Validate(RunConfig):
    pass


@attr.s
class Build(RunConfig):
    output_path = attr.ib()  # Path
    mount_point = attr.ib()  # str
