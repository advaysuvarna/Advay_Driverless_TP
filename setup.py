from setuptools import find_packages, setup

package_name = 'task_one_nodes'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
     entry_points={
        'console_scripts': [
            'publisher_node = task_one_nodes.publisher:main',
            'subscriber_node = task_one_nodes.subscriber:main',
        ],
    },
)
