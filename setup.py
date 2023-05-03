from setuptools import setup

def read_requirements(path: str):
    with open(path, "r", encoding="utf-8") as f:
        lines = (x.strip() for x in f.read().splitlines())
        return [x for x in lines if x and not x.startswith("#")]


setup(
    name="SuperMechs",
    author="Eneg",
    description="A Python library for SuperMechs",
    install_requires=read_requirements("requirements.txt"),
    python_requires=">=3.10.0",
)
