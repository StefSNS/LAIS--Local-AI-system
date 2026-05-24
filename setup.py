from setuptools import setup, find_packages

setup(
    name="lais-ai",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "customtkinter",
        "pillow",
        "psutil",
        "requests",
        "google-genai",
        "sounddevice",
        "PyQt6",
    ],
    entry_points={
        "console_scripts": [
            "lais=install:main",
        ],
    },
    python_requires=">=3.11",
)
