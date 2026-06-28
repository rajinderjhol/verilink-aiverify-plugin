from setuptools import setup, find_packages

setup(
    name="verilink-aiverify-plugin",
    version="1.1.0",
    description="VeriLinkOS Active Governance Integration for AI Verify",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.23.0,<0.28.0",
        "pydantic>=1.10.0,<3.0.0",
        "python-dotenv>=0.19.0,<2.1.0",
        "tenacity>=8.0.0,<9.1.0",
    ],
    entry_points={
        "aiverify.plugins": [
            "verilink_os = verilink_plugin.plugin:VeriLinkGovernancePlugin",
        ],
    },
    python_requires=">=3.9",
)
