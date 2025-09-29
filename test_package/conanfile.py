from conan import ConanFile


class TestPackageConan(ConanFile):
    settings = None
    generators = ("VirtualRunEnv",)
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def test(self):
        # Validate the package can be imported in a virtual run environment
        self.run(
            'python -c "import mcp_project_orchestrator as m; print(m.__version__)"',
            env="conanrun",
        )

