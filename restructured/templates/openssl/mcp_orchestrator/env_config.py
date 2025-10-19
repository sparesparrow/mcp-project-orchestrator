"""
Environment variable configuration and validation.

This module provides environment variable management with fallbacks
and clear error messages for required configuration.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class EnvVarConfig:
    """Configuration for an environment variable."""
    name: str
    required: bool
    default: Optional[str] = None
    description: str = ""
    validation_func: Optional[callable] = None


class EnvironmentConfig:
    """Manages environment variable configuration with fallbacks."""
    
    # Define environment variable configurations
    ENV_VARS = {
        "CONAN_USER_HOME": EnvVarConfig(
            name="CONAN_USER_HOME",
            required=False,
            description="Conan user home directory for package cache"
        ),
        "OPENSSL_ROOT_DIR": EnvVarConfig(
            name="OPENSSL_ROOT_DIR", 
            required=False,
            description="OpenSSL installation root directory"
        ),
        "CLOUDSMITH_API_KEY": EnvVarConfig(
            name="CLOUDSMITH_API_KEY",
            required=False,
            description="Cloudsmith API key for package publishing"
        ),
        "CONAN_REPOSITORY_NAME": EnvVarConfig(
            name="CONAN_REPOSITORY_NAME",
            required=False,
            description="Conan repository name for package publishing"
        ),
        "GITHUB_TOKEN": EnvVarConfig(
            name="GITHUB_TOKEN",
            required=False,
            description="GitHub token for repository access"
        ),
        "MCP_ORCHESTRATOR_OPT_OUT": EnvVarConfig(
            name="MCP_ORCHESTRATOR_OPT_OUT",
            required=False,
            description="Skip Cursor configuration deployment"
        ),
        "CURSOR_CONFIG_PATH": EnvVarConfig(
            name="CURSOR_CONFIG_PATH",
            required=False,
            description="Path to .cursor directory"
        ),
    }
    
    def __init__(self):
        self._cache: Dict[str, Optional[str]] = {}
    
    def get(self, var_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable with fallback.
        
        Args:
            var_name: Name of environment variable
            default: Default value if not set
            
        Returns:
            Environment variable value or default
        """
        if var_name in self._cache:
            return self._cache[var_name]
        
        value = os.getenv(var_name, default)
        self._cache[var_name] = value
        return value
    
    def get_conan_home(self) -> str:
        """Get Conan home directory with fallback."""
        conan_home = self.get("CONAN_USER_HOME")
        if conan_home:
            return conan_home
        
        # Default Conan home based on platform
        home = Path.home()
        return str(home / ".conan2")
    
    def get_openssl_root(self) -> Optional[str]:
        """Get OpenSSL root directory."""
        return self.get("OPENSSL_ROOT_DIR")
    
    def get_cloudsmith_api_key(self) -> Optional[str]:
        """Get Cloudsmith API key."""
        return self.get("CLOUDSMITH_API_KEY")
    
    def get_conan_repository_name(self) -> Optional[str]:
        """Get Conan repository name."""
        return self.get("CONAN_REPOSITORY_NAME")
    
    def get_github_token(self) -> Optional[str]:
        """Get GitHub token."""
        return self.get("GITHUB_TOKEN")
    
    def is_opt_out(self) -> bool:
        """Check if Cursor configuration is opted out."""
        opt_out = self.get("MCP_ORCHESTRATOR_OPT_OUT", "false")
        return opt_out.lower() in ("true", "1", "yes", "on")
    
    def get_cursor_config_path(self, repo_root: Path) -> Path:
        """Get Cursor configuration path."""
        config_path = self.get("CURSOR_CONFIG_PATH")
        if config_path:
            return Path(config_path)
        return repo_root / ".cursor"
    
    def validate_required(self, project_type: str) -> Tuple[bool, List[str]]:
        """
        Validate required environment variables for a project type.
        
        Args:
            project_type: Type of project (openssl, generic, etc.)
            
        Returns:
            Tuple of (all_valid, missing_vars)
        """
        missing_vars = []
        
        # Define required variables by project type
        required_vars = {
            "openssl": ["CONAN_USER_HOME", "OPENSSL_ROOT_DIR"],
            "generic": [],
        }
        
        project_required = required_vars.get(project_type, [])
        
        for var_name in project_required:
            if not self.get(var_name):
                missing_vars.append(var_name)
        
        return len(missing_vars) == 0, missing_vars
    
    def check_optional_vars(self, project_type: str) -> Dict[str, bool]:
        """
        Check status of optional environment variables.
        
        Args:
            project_type: Type of project
            
        Returns:
            Dictionary mapping variable names to presence status
        """
        optional_vars = {
            "openssl": ["CLOUDSMITH_API_KEY", "CONAN_REPOSITORY_NAME", "GITHUB_TOKEN"],
            "generic": ["CONAN_USER_HOME", "GITHUB_TOKEN"],
        }
        
        project_optional = optional_vars.get(project_type, [])
        status = {}
        
        for var_name in project_optional:
            status[var_name] = self.get(var_name) is not None
        
        return status
    
    def get_validation_errors(self, project_type: str) -> List[str]:
        """
        Get validation error messages for missing required variables.
        
        Args:
            project_type: Type of project
            
        Returns:
            List of error messages
        """
        errors = []
        is_valid, missing_vars = self.validate_required(project_type)
        
        if not is_valid:
            errors.append(f"Missing required environment variables for {project_type} project:")
            for var_name in missing_vars:
                var_config = self.ENV_VARS.get(var_name)
                if var_config:
                    errors.append(f"  - {var_name}: {var_config.description}")
                else:
                    errors.append(f"  - {var_name}")
            errors.append("")
            errors.append("Please set these variables and try again:")
            for var_name in missing_vars:
                errors.append(f"  export {var_name}=<value>")
        
        return errors
    
    def get_warnings(self, project_type: str) -> List[str]:
        """
        Get warning messages for missing optional variables.
        
        Args:
            project_type: Type of project
            
        Returns:
            List of warning messages
        """
        warnings = []
        optional_status = self.check_optional_vars(project_type)
        
        missing_optional = [var for var, present in optional_status.items() if not present]
        
        if missing_optional:
            warnings.append(f"Optional environment variables not set for {project_type} project:")
            for var_name in missing_optional:
                var_config = self.ENV_VARS.get(var_name)
                if var_config:
                    warnings.append(f"  - {var_name}: {var_config.description}")
                else:
                    warnings.append(f"  - {var_name}")
            warnings.append("")
            warnings.append("These variables may be needed for full functionality:")
            for var_name in missing_optional:
                warnings.append(f"  export {var_name}=<value>")
        
        return warnings
    
    def print_status(self, project_type: str, verbose: bool = False) -> None:
        """
        Print environment variable status.
        
        Args:
            project_type: Type of project
            verbose: Show detailed information
        """
        print(f"Environment variables for {project_type} project:")
        
        # Check required variables
        is_valid, missing_vars = self.validate_required(project_type)
        if missing_vars:
            print(f"  ❌ Missing required: {', '.join(missing_vars)}")
        else:
            print("  ✅ All required variables present")
        
        # Check optional variables
        optional_status = self.check_optional_vars(project_type)
        missing_optional = [var for var, present in optional_status.items() if not present]
        
        if missing_optional:
            print(f"  ⚠️  Missing optional: {', '.join(missing_optional)}")
        else:
            print("  ✅ All optional variables present")
        
        if verbose:
            print("\nDetailed status:")
            for var_name, var_config in self.ENV_VARS.items():
                value = self.get(var_name)
                status = "✅" if value else "❌"
                print(f"  {status} {var_name}: {value or 'Not set'}")
                if var_config.description:
                    print(f"      {var_config.description}")


# Global instance
env_config = EnvironmentConfig()


def get_environment_config() -> EnvironmentConfig:
    """Get the global environment configuration instance."""
    return env_config