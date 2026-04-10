import sysconfig
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop


def _run_shortcut():
    try:
        from macro_database.run import create_shortcut
        create_shortcut()
    except Exception as e:
        print(f"Warning: Could not create desktop shortcut: {e}")


class PostInstall(install):
    def run(self):
        install.run(self)
        _run_shortcut()


class PostDevelop(develop):
    def run(self):
        develop.run(self)
        _run_shortcut()


setup(
    packages=find_packages(),
    include_package_data=True,
    # Install the .pth file to site-packages so Python runs the shortcut
    # hook on the next startup after any pip install (including pip+git).
    data_files=[
        (sysconfig.get_path('purelib'), ['macro_database_post_install.pth'])
    ],
    cmdclass={
        'install': PostInstall,
        'develop': PostDevelop,
    },
)
