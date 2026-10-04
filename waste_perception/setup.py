from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'waste_perception'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(
        include=[
            package_name,
            package_name + ".*",
        ]
    ),

    data_files=[

        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),

        (
            "share/" + package_name,
            ["package.xml"],
        ),

        (
            os.path.join(
                "share",
                package_name,
                "launch",
            ),
            glob("launch/*.launch.py"),
        ),

        (
            os.path.join("share", package_name, "config"),
            glob("config/*.yaml"),
        ),
    ],

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='pedakolimi.harish@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        "console_scripts": [

            "object_spawner = "
            "waste_perception.object_spawner:main",

            "vision_processor = "
            "waste_perception.vision_processor:main",

            "task_manager = "
            "waste_perception.task_manager:main",

        ],
    },
)
