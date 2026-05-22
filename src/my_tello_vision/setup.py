from setuptools import setup
import os
from glob import glob

package_name = 'my_tello_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # This line makes sure your launch files are copied to the install folder
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mahmmudqatmh',
    maintainer_email='mahmmudqatmh@todo.todo',
    description='Tello Vision Control with YOLO',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            #
	    'tello_vision_control = my_tello_vision.tello_vision_control:main',
            'calibrate = my_tello_vision.calibrate:main',
            'record_tello = my_tello_vision.record_tello:main',
            'record_tello_raw = my_tello_vision.record_tello_raw:main'
        ],
    },
)
