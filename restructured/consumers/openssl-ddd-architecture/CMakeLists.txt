cmake_minimum_required(VERSION 3.15)
project(OpenSSLDDDArchitecture VERSION 0.2.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# DDD Architecture Configuration
option(ENABLE_FIPS "Enable FIPS compliance" ON)
option(ENABLE_DDD_LAYERS "Enable DDD layer separation" ON)
option(ENABLE_MCP_INTEGRATION "Enable MCP integration" ON)
option(ENABLE_SIDE_CHANNEL_ANALYSIS "Enable side channel analysis" ON)

# Include directories for each layer
include_directories(
    src/domain/crypto
    src/application/ssl
    src/infrastructure/providers
    src/presentation/apps
    include
)

# Source files organized by DDD layers
set(DOMAIN_SOURCES
    src/domain/crypto/aes.c
    src/domain/crypto/sha256.c
    src/domain/crypto/rsa.c
    src/domain/crypto/ec.c
)

set(APPLICATION_SOURCES
    src/application/ssl/tls1_3.c
    src/application/ssl/handshake.c
    src/application/ssl/record.c
    src/application/ssl/verify.c
)

set(INFRASTRUCTURE_SOURCES
    src/infrastructure/providers/fips_provider.c
    src/infrastructure/providers/hsm_provider.c
    src/infrastructure/providers/tpm_provider.c
)

set(PRESENTATION_SOURCES
    src/presentation/apps/openssl_cli.c
    src/presentation/apps/openssl_api.c
)

# Header files
set(HEADERS
    include/openssl_ddd.h
    src/domain/crypto/aes.h
    src/domain/crypto/sha256.h
    src/domain/crypto/rsa.h
    src/domain/crypto/ec.h
    src/application/ssl/tls1_3.h
    src/application/ssl/handshake.h
    src/application/ssl/record.h
    src/application/ssl/verify.h
    src/infrastructure/providers/fips_provider.h
    src/infrastructure/providers/hsm_provider.h
    src/infrastructure/providers/tpm_provider.h
    src/presentation/apps/openssl_cli.h
    src/presentation/apps/openssl_api.h
)

# Create libraries for each DDD layer
add_library(openssl_ddd_domain ${DOMAIN_SOURCES})
add_library(openssl_ddd_application ${APPLICATION_SOURCES})
add_library(openssl_ddd_infrastructure ${INFRASTRUCTURE_SOURCES})
add_library(openssl_ddd_presentation ${PRESENTATION_SOURCES})

# Set target properties
set_target_properties(openssl_ddd_domain PROPERTIES
    C_STANDARD 11
    C_STANDARD_REQUIRED ON
    POSITION_INDEPENDENT_CODE ON
)

set_target_properties(openssl_ddd_application PROPERTIES
    C_STANDARD 11
    C_STANDARD_REQUIRED ON
    POSITION_INDEPENDENT_CODE ON
)

set_target_properties(openssl_ddd_infrastructure PROPERTIES
    C_STANDARD 11
    C_STANDARD_REQUIRED ON
    POSITION_INDEPENDENT_CODE ON
)

set_target_properties(openssl_ddd_presentation PROPERTIES
    C_STANDARD 11
    C_STANDARD_REQUIRED ON
    POSITION_INDEPENDENT_CODE ON
)

# DDD Layer Dependencies (enforced by CMake)
target_link_libraries(openssl_ddd_application openssl_ddd_domain)
target_link_libraries(openssl_ddd_infrastructure openssl_ddd_domain)
target_link_libraries(openssl_ddd_presentation openssl_ddd_application)

# Create main library
add_library(openssl_ddd_architecture ${DOMAIN_SOURCES} ${APPLICATION_SOURCES} ${INFRASTRUCTURE_SOURCES} ${PRESENTATION_SOURCES})

# Link all layers
target_link_libraries(openssl_ddd_architecture
    openssl_ddd_domain
    openssl_ddd_application
    openssl_ddd_infrastructure
    openssl_ddd_presentation
)

# FIPS Configuration
if(ENABLE_FIPS)
    target_compile_definitions(openssl_ddd_architecture PRIVATE
        FIPS_MODE=1
        OPENSSL_FIPS=1
        FIPS_140_3=1
    )
    
    # Find FIPS dependencies
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(FIPS REQUIRED fips-crypto)
    target_link_libraries(openssl_ddd_architecture ${FIPS_LIBRARIES})
    target_include_directories(openssl_ddd_architecture PRIVATE ${FIPS_INCLUDE_DIRS})
endif()

# MCP Integration
if(ENABLE_MCP_INTEGRATION)
    target_compile_definitions(openssl_ddd_architecture PRIVATE
        MCP_INTEGRATION=1
        MCP_ORCHESTRATION=1
    )
    
    # Find MCP dependencies
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(MCP REQUIRED mcp-project-orchestrator)
    target_link_libraries(openssl_ddd_architecture ${MCP_LIBRARIES})
    target_include_directories(openssl_ddd_architecture PRIVATE ${MCP_INCLUDE_DIRS})
endif()

# Side Channel Analysis
if(ENABLE_SIDE_CHANNEL_ANALYSIS)
    target_compile_definitions(openssl_ddd_architecture PRIVATE
        SIDE_CHANNEL_ANALYSIS=1
        SIDE_CHANNEL_PROTECTION=1
    )
    
    # Find side channel analysis tools
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(SIDE_CHANNEL REQUIRED valgrind)
    target_link_libraries(openssl_ddd_architecture ${SIDE_CHANNEL_LIBRARIES})
    target_include_directories(openssl_ddd_architecture PRIVATE ${SIDE_CHANNEL_INCLUDE_DIRS})
endif()

# System libraries
if(UNIX)
    target_link_libraries(openssl_ddd_architecture pthread dl)
elseif(WIN32)
    target_link_libraries(openssl_ddd_architecture ws2_32 crypt32)
endif()

# Create executables for each layer (for testing)
add_executable(domain_test src/domain/crypto/test_domain.c)
target_link_libraries(domain_test openssl_ddd_domain)

add_executable(application_test src/application/ssl/test_application.c)
target_link_libraries(application_test openssl_ddd_application openssl_ddd_domain)

add_executable(infrastructure_test src/infrastructure/providers/test_infrastructure.c)
target_link_libraries(infrastructure_test openssl_ddd_infrastructure openssl_ddd_domain)

add_executable(presentation_test src/presentation/apps/test_presentation.c)
target_link_libraries(presentation_test openssl_ddd_presentation openssl_ddd_application openssl_ddd_domain)

# Main OpenSSL CLI executable
add_executable(openssl_cli src/presentation/apps/openssl_cli.c)
target_link_libraries(openssl_cli openssl_ddd_architecture)

# Install targets
install(TARGETS openssl_ddd_architecture
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(TARGETS openssl_cli
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/ DESTINATION include)

# Install headers for each layer
install(FILES ${HEADERS} DESTINATION include)

# Create pkg-config file
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/openssl-ddd-architecture.pc.in
    ${CMAKE_CURRENT_BINARY_DIR}/openssl-ddd-architecture.pc
    @ONLY
)

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/openssl-ddd-architecture.pc
    DESTINATION lib/pkgconfig
)

# CPack configuration for packaging
set(CPACK_PACKAGE_NAME "openssl-ddd-architecture")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "OpenSSL with Domain Driven Design Architecture")
set(CPACK_PACKAGE_VENDOR "sparesparrow")
set(CPACK_PACKAGE_CONTACT "https://github.com/sparesparrow/openssl-ddd-architecture")

# Include CPack
include(CPack)