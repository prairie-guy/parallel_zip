#!/usr/bin/env python
"""Setup script for parallel_zip."""

from setuptools import setup
from setuptools.command.install import install
import subprocess
import warnings

class PostInstallCommand(install):
    """Post-installation check for GNU parallel."""
    def run(self):
        install.run(self)
        try:
            subprocess.run(["parallel", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            warnings.warn(
                "\n" + "="*60 + "\n" +
                "WARNING: GNU parallel not found!\n" +
                "parallel_zip requires GNU parallel to be installed.\n\n" +
                "Please install it using:\n" +
                "  Ubuntu/Debian: sudo apt-get install parallel\n" +
                "  CentOS/RHEL: sudo yum install parallel\n" +
                "  macOS: brew install parallel\n\n" +
                "See: https://www.gnu.org/software/parallel/\n" +
                "="*60
            )

if __name__ == "__main__":
    setup(cmdclass={'install': PostInstallCommand})
