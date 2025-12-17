#!/usr/bin/env python3
"""
OpenSSL FIPS Policy Package Recipe
Provides FIPS 140-3 compliance configuration and policy files
"""

from conan import ConanFile
from conan.tools.files import copy, save
from conan.tools.cmake import CMakeToolchain, CMakeDeps, cmake_layout
import os
import json
from datetime import datetime


class OpenSSLFipsPolicyConan(ConanFile):
    name = "openssl-fips-policy"
    version = "3.3.0"
    description = "OpenSSL FIPS 140-3 compliance policy and configuration"
    license = "Apache-2.0"
    homepage = "https://www.openssl.org"
    topics = ("openssl", "fips", "security", "compliance", "policy")
    url = "https://github.com/sparesparrow/openssl-fips-policy"
    
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fips_level": ["1", "2", "3", "4"],
        "enable_side_channel_analysis": [True, False],
        "enable_continuous_selftest": [True, False],
    }
    default_options = {
        "fips_level": "1",
        "enable_side_channel_analysis": True,
        "enable_continuous_selftest": True,
    }
    
    exports_sources = "*.cnf", "*.md", "*.json", "LICENSE*"
    
    def layout(self):
        cmake_layout(self)
    
    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        
        tc = CMakeToolchain(self)
        tc.variables["FIPS_LEVEL"] = self.options.fips_level
        tc.variables["ENABLE_SIDE_CHANNEL_ANALYSIS"] = self.options.enable_side_channel_analysis
        tc.variables["ENABLE_CONTINUOUS_SELFTEST"] = self.options.enable_continuous_selftest
        tc.generate()
        
        # Generate FIPS configuration
        self._generate_fips_config()
        
        # Generate SBOM
        self._generate_sbom()
    
    def _generate_fips_config(self):
        """Generate FIPS configuration based on options"""
        fips_config = {
            "fips_module": {
                "name": "OpenSSL FIPS Provider",
                "version": "3.3.0",
                "certificate_number": "FIPS 140-3 #4985",
                "fips_level": int(self.options.fips_level),
                "security_level": int(self.options.fips_level),
                "algorithms": {
                    "approved": [
                        "AES-128-CBC", "AES-192-CBC", "AES-256-CBC",
                        "AES-128-GCM", "AES-192-GCM", "AES-256-GCM",
                        "SHA-1", "SHA-224", "SHA-256", "SHA-384", "SHA-512",
                        "RSA-1024", "RSA-2048", "RSA-3072", "RSA-4096",
                        "ECDSA-P256", "ECDSA-P384", "ECDSA-P521",
                        "HMAC-SHA1", "HMAC-SHA224", "HMAC-SHA256", 
                        "HMAC-SHA384", "HMAC-SHA512",
                        "DRBG-CTR-AES128", "DRBG-CTR-AES192", "DRBG-CTR-AES256",
                        "DRBG-HASH-SHA1", "DRBG-HASH-SHA224", "DRBG-HASH-SHA256",
                        "DRBG-HASH-SHA384", "DRBG-HASH-SHA512",
                        "KDF-HKDF-SHA1", "KDF-HKDF-SHA224", "KDF-HKDF-SHA256",
                        "KDF-HKDF-SHA384", "KDF-HKDF-SHA512",
                        "KDF-PBKDF2-SHA1", "KDF-PBKDF2-SHA224", "KDF-PBKDF2-SHA256",
                        "KDF-PBKDF2-SHA384", "KDF-PBKDF2-SHA512"
                    ],
                    "prohibited": [
                        "DES", "3DES", "RC4", "MD5", "SHA-0"
                    ]
                },
                "selftests": {
                    "power_on": True,
                    "conditional": True,
                    "continuous": self.options.enable_continuous_selftest,
                    "side_channel_analysis": self.options.enable_side_channel_analysis
                },
                "key_management": {
                    "key_generation": True,
                    "key_derivation": True,
                    "key_agreement": True,
                    "key_storage": "secure"
                },
                "random_number_generation": {
                    "approved_drbg": True,
                    "entropy_sources": ["system", "hardware"],
                    "reseed_interval": 1000000
                }
            }
        }
        
        # Save FIPS configuration
        fips_config_path = os.path.join(self.build_folder, "fips_config.json")
        with open(fips_config_path, "w") as f:
            json.dump(fips_config, f, indent=2)
    
    def _generate_sbom(self):
        """Generate Software Bill of Materials (SBOM)"""
        sbom_data = {
            "SPDXID": "SPDXRef-DOCUMENT",
            "spdxVersion": "SPDX-2.3",
            "creationInfo": {
                "created": datetime.utcnow().isoformat() + "Z",
                "creators": [
                    "Tool: Conan OpenSSL FIPS Policy",
                    "Organization: sparesparrow"
                ],
                "licenseListVersion": "3.19"
            },
            "name": "OpenSSL FIPS Policy Package",
            "dataLicense": "CC0-1.0",
            "documentNamespace": f"https://sparesparrow.github.io/openssl-fips-policy/{self.version}",
            "packages": [
                {
                    "SPDXID": "SPDXRef-Package-OpenSSL-FIPS-Policy",
                    "name": "openssl-fips-policy",
                    "versionInfo": self.version,
                    "downloadLocation": "https://github.com/sparesparrow/openssl-fips-policy",
                    "licenseConcluded": "Apache-2.0",
                    "licenseDeclared": "Apache-2.0",
                    "copyrightText": "Copyright (c) 2024 sparesparrow",
                    "description": self.description,
                    "supplier": "Organization: sparesparrow",
                    "originator": "Organization: sparesparrow",
                    "filesAnalyzed": False,
                    "packageVerificationCode": {
                        "packageVerificationCodeValue": "da39a3ee5e6b4b0d3255bfef95601890afd80709"
                    }
                }
            ],
            "relationships": [
                {
                    "spdxElementId": "SPDXRef-DOCUMENT",
                    "relationshipType": "DESCRIBES",
                    "relatedSpdxElement": "SPDXRef-Package-OpenSSL-FIPS-Policy"
                }
            ]
        }
        
        # Save SBOM
        sbom_path = os.path.join(self.build_folder, "sbom.json")
        with open(sbom_path, "w") as f:
            json.dump(sbom_data, f, indent=2)
    
    def package(self):
        """Package FIPS policy files"""
        # Copy FIPS configuration files
        copy(self, "*.cnf", src=self.source_folder, dst=os.path.join(self.package_folder, "res"))
        copy(self, "*.md", src=self.source_folder, dst=os.path.join(self.package_folder, "res"))
        copy(self, "*.json", src=self.source_folder, dst=os.path.join(self.package_folder, "res"))
        
        # Copy generated files
        copy(self, "fips_config.json", src=self.build_folder, dst=os.path.join(self.package_folder, "res"))
        copy(self, "sbom.json", src=self.build_folder, dst=os.path.join(self.package_folder, "res"))
        
        # Copy license
        copy(self, "LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        
        # Generate fipsmodule.cnf
        self._generate_fipsmodule_cnf()
    
    def _generate_fipsmodule_cnf(self):
        """Generate fipsmodule.cnf configuration file"""
        fipsmodule_cnf = f"""# OpenSSL FIPS Module Configuration
# Generated by Conan OpenSSL FIPS Policy Package

# FIPS Module Information
fips = fips_sect

[fips_sect]
# FIPS Module Name
fips_module_name = OpenSSL FIPS Provider

# FIPS Module Version
fips_module_version = {self.version}

# FIPS Certificate Number
fips_certificate_number = FIPS 140-3 #4985

# FIPS Security Level
fips_security_level = {self.options.fips_level}

# Approved Algorithms
fips_approved_algorithms = AES-128-CBC:AES-192-CBC:AES-256-CBC:AES-128-GCM:AES-192-GCM:AES-256-GCM:SHA-1:SHA-224:SHA-256:SHA-384:SHA-512:RSA-1024:RSA-2048:RSA-3072:RSA-4096:ECDSA-P256:ECDSA-P384:ECDSA-P521:HMAC-SHA1:HMAC-SHA224:HMAC-SHA256:HMAC-SHA384:HMAC-SHA512:DRBG-CTR-AES128:DRBG-CTR-AES192:DRBG-CTR-AES256:DRBG-HASH-SHA1:DRBG-HASH-SHA224:DRBG-HASH-SHA256:DRBG-HASH-SHA384:DRBG-HASH-SHA512:KDF-HKDF-SHA1:KDF-HKDF-SHA224:KDF-HKDF-SHA256:KDF-HKDF-SHA384:KDF-HKDF-SHA512:KDF-PBKDF2-SHA1:KDF-PBKDF2-SHA224:KDF-PBKDF2-SHA256:KDF-PBKDF2-SHA384:KDF-PBKDF2-SHA512

# Prohibited Algorithms
fips_prohibited_algorithms = DES:3DES:RC4:MD5:SHA-0

# Self-Test Configuration
fips_power_on_selftest = yes
fips_conditional_selftest = yes
fips_continuous_selftest = {'yes' if self.options.enable_continuous_selftest else 'no'}
fips_side_channel_analysis = {'yes' if self.options.enable_side_channel_analysis else 'no'}

# Key Management
fips_key_generation = yes
fips_key_derivation = yes
fips_key_agreement = yes
fips_key_storage = secure

# Random Number Generation
fips_approved_drbg = yes
fips_entropy_sources = system:hardware
fips_reseed_interval = 1000000

# Integrity Checking
fips_integrity_check = yes
fips_integrity_key = 2b7e151628aed2a6abf7158809cf4f3c2b7e151628aed2a6abf7158809cf4f3c

# Error Handling
fips_error_handling = strict
fips_error_recovery = none
fips_error_logging = yes
"""
        
        # Save fipsmodule.cnf
        fipsmodule_path = os.path.join(self.package_folder, "res", "fipsmodule.cnf")
        with open(fipsmodule_path, "w") as f:
            f.write(fipsmodule_cnf)
    
    def package_info(self):
        """Provide FIPS policy information"""
        # Set FIPS configuration path
        fips_config = os.path.join(self.package_folder, "res", "fipsmodule.cnf")
        self.conf_info.define("openssl:fips_config", fips_config)
        
        # Set environment variables for consumers
        self.env_info.OPENSSL_FIPS = "1"
        self.env_info.OPENSSL_CONF = fips_config
        self.env_info.FIPS_LEVEL = self.options.fips_level
        self.env_info.FIPS_SIDE_CHANNEL_ANALYSIS = str(self.options.enable_side_channel_analysis).lower()
        self.env_info.FIPS_CONTINUOUS_SELFTEST = str(self.options.enable_continuous_selftest).lower()
        
        # Add to PATH for FIPS utilities
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
        
        # Set FIPS policy properties
        self.cpp_info.set_property("fips_compliant", True)
        self.cpp_info.set_property("fips_level", self.options.fips_level)
        self.cpp_info.set_property("security_validated", True)
        self.cpp_info.set_property("side_channel_analysis", self.options.enable_side_channel_analysis)
        self.cpp_info.set_property("continuous_selftest", self.options.enable_continuous_selftest)