import pathlib

LANGUAGE_EXTENSIONS = {
    # C/C++ (Robotics core controllers, ROS C++ nodes)
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".h": "c_cpp_header",
    ".hh": "cpp",
    ".c": "c",
    # Python (ROS/ROS2 nodes, scripts, ML)
    ".py": "python",
    ".pyi": "python",
    # Embedded & Microcontroller
    ".ino": "arduino",
    ".pde": "arduino",
    ".dts": "devicetree",
    ".dtsi": "devicetree",
    # Robotics Description & Launch
    ".urdf": "urdf",
    ".xacro": "xacro",
    ".sdf": "sdf",
    ".msg": "ros_msg",
    ".srv": "ros_srv",
    ".action": "ros_action",
    # Rust (Robotics high reliability)
    ".rs": "rust",
    # Build & Packages
    ".cmake": "cmake",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".sh": "shell",
    ".bash": "shell",
    ".md": "markdown",
    ".txt": "text",
}

SPECIAL_FILENAMES = {
    "CMakeLists.txt": "cmake",
    "package.xml": "ros_package_xml",
    "Makefile": "makefile",
    "Dockerfile": "dockerfile",
    "render.yaml": "yaml",
}

def detect_language(file_path: str) -> str:
    path = pathlib.Path(file_path)
    name = path.name

    if name in SPECIAL_FILENAMES:
        return SPECIAL_FILENAMES[name]

    # Handle .launch.py, .launch.xml
    if ".launch.py" in name:
        return "ros2_launch_py"
    if ".launch.xml" in name or name.endswith(".launch"):
        return "ros_launch_xml"

    suffix = path.suffix.lower()
    return LANGUAGE_EXTENSIONS.get(suffix, "plaintext")
